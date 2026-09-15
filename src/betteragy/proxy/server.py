"""Asyncio TCP & TLS MITM proxy server for Antigravity Google API traffic."""

import asyncio
import logging
import ssl
from typing import Optional, Set

from ..services.cert_service import CertService
from .interceptor import ProxyInterceptor
from .stream_utils import ProxyStreamReaderProtocol, read_chunked_payload

logger = logging.getLogger("betteragy.proxy")
DEFAULT_PROXY_HOST, DEFAULT_PROXY_PORT = "127.0.0.1", 45124


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
        self._active_tasks: Set[asyncio.Task] = set()

    async def start(self) -> None:
        """Start the proxy server listener."""
        self.ssl_ctx = self.cert_service.get_server_ssl_context()
        self._server = await asyncio.start_server(self._client_handler_entry, self.host, self.port)
        logger.info("[Proxy] [ok] Listening on http://%s:%d", self.host, self.port)

    def _client_handler_entry(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """Prevent task GC collection while connection is active."""
        task = asyncio.create_task(self._handle_client(reader, writer))
        self._active_tasks.add(task)
        task.add_done_callback(self._active_tasks.discard)

    async def stop(self) -> None:
        """Gracefully close listener and active connections."""
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        for t in list(self._active_tasks):
            t.cancel()
        if self._active_tasks:
            await asyncio.gather(*self._active_tasks, return_exceptions=True)
            self._active_tasks.clear()

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
                return
            parts = req_line_bytes.decode("utf-8", errors="replace").strip().split()
            if not parts:
                return
            if parts[0].upper() == "CONNECT":
                await self._handle_connect(parts[1], reader, writer)
            else:
                await self._handle_plain_http(parts[1], reader, writer)
        except (ConnectionResetError, BrokenPipeError, asyncio.CancelledError):
            pass
        except Exception as e:
            logger.debug("[Proxy] Client handler error: %s", e)
        finally:
            try:
                if not writer.is_closing():
                    writer.close()
                    await writer.wait_closed()
            except Exception:
                pass

    async def _handle_plain_http(self, path: str, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """Handle direct HTTP health check requests."""
        while (line := await reader.readline()) and line != b"\r\n":
            pass
        if path in ("/health", "/status"):
            acc = self.interceptor.account_service.get_active_account()
            body = f'{{"status": "ok", "service": "betteragy-proxy", "active_account": "{acc.email if acc else "none"}"}}\n'
            resp = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {len(body)}\r\n\r\n{body}"
        else:
            resp = "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n"
        writer.write(resp.encode("utf-8"))
        await writer.drain()

    async def _handle_connect(
        self, target: str, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Handle CONNECT tunnel and perform TLS MITM for Google APIs."""
        while (line := await reader.readline()) and line != b"\r\n":
            pass
        host, port_str = target.split(":", 1) if ":" in target else (target, "443")
        port = int(port_str)
        writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        await writer.drain()

        if host.endswith(".googleapis.com"):
            loop = asyncio.get_running_loop()
            tls_reader = asyncio.StreamReader(limit=16 * 1024 * 1024)
            protocol = ProxyStreamReaderProtocol(tls_reader)
            tls_transport = await loop.start_tls(
                writer.transport, protocol=protocol, sslcontext=self.ssl_ctx, server_side=True
            )
            tls_writer = asyncio.StreamWriter(tls_transport, protocol, tls_reader, loop)
            try:
                await self._process_tls_requests(tls_reader, tls_writer, host, port)
            finally:
                try:
                    if not tls_writer.is_closing():
                        tls_writer.close()
                        await tls_writer.wait_closed()
                except Exception:
                    pass
        else:
            await self._tunnel_raw_tcp(host, port, reader, writer)

    async def _process_tls_requests(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, host: str, port: int
    ) -> None:
        """Parse HTTP requests inside decrypted TLS stream and forward to interceptor."""
        while True:
            try:
                req_line_bytes = await reader.readline()
            except (asyncio.IncompleteReadError, ConnectionResetError, BrokenPipeError, ssl.SSLError):
                break
            if not req_line_bytes:
                break
            parts = req_line_bytes.decode("utf-8", errors="replace").strip().split()
            if len(parts) < 2:
                break
            method, path = parts[0], parts[1]
            headers, content_length, is_chunked = {}, 0, False

            while (line := await reader.readline()) and line != b"\r\n":
                header_text = line.decode("utf-8", errors="replace").strip()
                if ":" in header_text:
                    k, v = [x.strip() for x in header_text.split(":", 1)]
                    headers[k] = v
                    if k.lower() == "content-length":
                        content_length = int(v)
                    elif k.lower() == "transfer-encoding" and "chunked" in v.lower():
                        is_chunked = True

            if headers.get("expect", "").strip().lower() == "100-continue":
                writer.write(b"HTTP/1.1 100 Continue\r\n\r\n")
                await writer.drain()

            if is_chunked:
                body = await read_chunked_payload(reader)
            elif content_length > 0:
                body = await reader.readexactly(content_length)
            else:
                body = b""

            should_close = await self.interceptor.forward_request(method, path, headers, body, host, port, writer)
            if should_close or headers.get("connection", "").strip().lower() == "close":
                break

    async def _tunnel_raw_tcp(
        self, host: str, port: int, client_reader: asyncio.StreamReader, client_writer: asyncio.StreamWriter
    ) -> None:
        """Bidirectional pipe for unintercepted non-Google hosts."""
        try:
            up_reader, up_writer = await asyncio.open_connection(host, port)

            async def pipe(r, w):
                try:
                    while buf := await r.read(16384):
                        w.write(buf)
                        await w.drain()
                except Exception:
                    pass
                finally:
                    if not w.is_closing():
                        w.close()

            await asyncio.gather(pipe(client_reader, up_writer), pipe(up_reader, client_writer))
        except Exception as e:
            logger.debug("[Proxy] Raw TCP tunnel error to %s:%d: %s", host, port, e)
