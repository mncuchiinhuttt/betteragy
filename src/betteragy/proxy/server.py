"""Asyncio TCP & TLS MITM proxy server for Antigravity Google API traffic."""

import asyncio
import logging
import ssl
from typing import Optional

from ..services.cert_service import CertService
from .interceptor import ProxyInterceptor
from .stream_utils import read_chunked_payload

logger = logging.getLogger("betteragy.proxy")
DEFAULT_PROXY_HOST = "127.0.0.1"
DEFAULT_PROXY_PORT = 45124


class BetteragyProxyServer:
    """HTTP CONNECT & TLS MITM proxy for zero-restart account switching."""

    def __init__(
        self,
        host: str = DEFAULT_PROXY_HOST,
        port: int = DEFAULT_PROXY_PORT,
        interceptor: Optional[ProxyInterceptor] = None,
        cert_service: Optional[CertService] = None,
    ):
        self.host, self.port = host, port
        self.interceptor = interceptor or ProxyInterceptor()
        self.cert_service = cert_service or CertService()
        self.ssl_ctx: Optional[ssl.SSLContext] = None
        self._server: Optional[asyncio.Server] = None

    async def start(self) -> None:
        """Start the proxy server listener."""
        self.ssl_ctx = self.cert_service.get_server_ssl_context()
        self._server = await asyncio.start_server(self._handle_client, self.host, self.port)
        logger.info("[Proxy] [ok] Listening on http://%s:%d", self.host, self.port)

    async def stop(self) -> None:
        """Gracefully close listener and active connections."""
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def serve_forever(self) -> None:
        """Run proxy server event loop."""
        if not self._server:
            await self.start()
        async with self._server:
            await self._server.serve_forever()

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """Handle incoming client connection."""
        try:
            req_line_bytes = await reader.readline()
            if not req_line_bytes:
                writer.close()
                return
            req_line = req_line_bytes.decode("utf-8", errors="replace").strip()
            parts = req_line.split()
            if not parts:
                writer.close()
                return
            method = parts[0].upper()
            if method == "CONNECT":
                await self._handle_connect(parts[1], reader, writer)
            else:
                await self._handle_plain_http(method, parts[1], reader, writer)
        except Exception as e:
            logger.debug("[Proxy] Client handler error: %s", e)
        finally:
            if not writer.is_closing():
                writer.close()

    async def _handle_plain_http(
        self, method: str, path: str, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Handle direct HTTP health check requests."""
        while True:
            line = await reader.readline()
            if not line or line == b"\r\n":
                break
        if path in ("/health", "/status"):
            active = self.interceptor.account_service.get_active_account()
            email = active.email if active else "none"
            body = f'{{"status": "ok", "service": "betteragy-proxy", "active_account": "{email}"}}\n'
            resp = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {len(body)}\r\n\r\n{body}"
        else:
            resp = "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n"
        writer.write(resp.encode("utf-8"))
        await writer.drain()

    async def _handle_connect(
        self, target: str, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Handle CONNECT tunnel and perform TLS MITM for Google APIs."""
        while True:
            line = await reader.readline()
            if not line or line == b"\r\n":
                break
        host, port_str = target.split(":", 1) if ":" in target else (target, "443")
        port = int(port_str)
        writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        await writer.drain()

        if host.endswith(".googleapis.com"):
            loop = asyncio.get_running_loop()
            tls_reader = asyncio.StreamReader()
            protocol = asyncio.StreamReaderProtocol(tls_reader)
            tls_transport = await loop.start_tls(writer.transport, protocol=protocol, sslcontext=self.ssl_ctx, server_side=True)
            tls_writer = asyncio.StreamWriter(tls_transport, protocol, tls_reader, loop)
            try:
                await self._process_tls_requests(tls_reader, tls_writer, host, port)
            finally:
                if not tls_writer.is_closing():
                    tls_writer.close()
        else:
            await self._tunnel_raw_tcp(host, port, reader, writer)

    async def _process_tls_requests(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, host: str, port: int
    ) -> None:
        """Parse HTTP requests inside decrypted TLS stream and forward to interceptor."""
        while True:
            req_line_bytes = await reader.readline()
            if not req_line_bytes:
                break
            req_line = req_line_bytes.decode("utf-8", errors="replace").strip()
            parts = req_line.split()
            if len(parts) < 2:
                break
            method, path = parts[0], parts[1]
            headers, content_length, is_chunked = {}, 0, False

            while True:
                line = await reader.readline()
                if not line or line == b"\r\n":
                    break
                header_text = line.decode("utf-8", errors="replace").strip()
                if ":" in header_text:
                    k, v = header_text.split(":", 1)
                    k_lower = k.strip().lower()
                    headers[k.strip()] = v.strip()
                    if k_lower == "content-length":
                        content_length = int(v.strip())
                    elif k_lower == "transfer-encoding" and "chunked" in v.strip().lower():
                        is_chunked = True

            if is_chunked:
                body = await read_chunked_payload(reader)
            elif content_length > 0:
                body = await reader.readexactly(content_length)
            else:
                body = b""

            await self.interceptor.forward_request(method, path, headers, body, host, port, writer)
            if headers.get("connection", "").lower() == "close":
                break

    async def _tunnel_raw_tcp(
        self, host: str, port: int, client_reader: asyncio.StreamReader, client_writer: asyncio.StreamWriter
    ) -> None:
        """Bidirectional pipe for unintercepted non-Google hosts."""
        try:
            up_reader, up_writer = await asyncio.open_connection(host, port)

            async def pipe(r, w):
                try:
                    while True:
                        buf = await r.read(16384)
                        if not buf:
                            break
                        w.write(buf)
                        await w.drain()
                except Exception:
                    pass

            await asyncio.gather(pipe(client_reader, up_writer), pipe(up_reader, client_writer))
        except Exception as e:
            logger.debug("[Proxy] Raw TCP tunnel error to %s:%d: %s", host, port, e)
