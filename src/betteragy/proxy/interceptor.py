"""Proxy interceptor: token swapping, 429 quota interception, and auto-rotation."""

import asyncio
import logging
import re
from typing import Dict, Optional

from ..services.account_service import AccountService
from ..services.rotation_service import RotationService

logger = logging.getLogger("betteragy.proxy")


class ProxyInterceptor:
    """Intercepts upstream requests, swaps Bearer tokens, and retries on 429."""

    def __init__(
        self,
        account_service: Optional[AccountService] = None,
        rotation_service: Optional[RotationService] = None,
    ):
        self.account_service = account_service or AccountService()
        self.rotation_service = rotation_service or RotationService(self.account_service)

    async def forward_request(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        body: bytes,
        upstream_host: str,
        upstream_port: int,
        client_writer: asyncio.StreamWriter,
    ) -> None:
        """Forward request to upstream with token swapping and auto-rotation on 429."""
        max_retries = 3
        attempt = 0

        # Strip hop-by-hop and connection headers
        cleaned_headers = {
            k: v for k, v in headers.items()
            if k.lower() not in ("connection", "keep-alive", "proxy-authenticate", "proxy-authorization")
        }
        cleaned_headers["Host"] = upstream_host

        while attempt < max_retries:
            attempt += 1
            active_acc = self.account_service.get_active_account()
            if active_acc:
                try:
                    token = self.account_service.ensure_valid_access_token(active_acc)
                    cleaned_headers["Authorization"] = f"Bearer {token}"
                    logger.info("[Proxy] [~] Injected token for active account: %s", active_acc.email)
                except Exception as e:
                    logger.warning("[Proxy] [!] Failed to refresh token for %s: %s", active_acc.email, e)

            # Connect to upstream Google server
            upstream_reader = None
            upstream_writer = None
            try:
                upstream_reader, upstream_writer = await asyncio.wait_for(
                    asyncio.open_connection(upstream_host, upstream_port, ssl=True),
                    timeout=10.0,
                )

                # Send request
                req_line = f"{method} {path} HTTP/1.1\r\n"
                headers_data = "".join(f"{k}: {v}\r\n" for k, v in cleaned_headers.items())
                upstream_writer.write((req_line + headers_data + "\r\n").encode("utf-8") + body)
                await upstream_writer.drain()

                # Read response status line
                status_line = await upstream_reader.readline()
                if not status_line:
                    raise IOError("Empty response from upstream")

                match = re.match(r"^HTTP/\d\.\d\s+(\d+)", status_line.decode("utf-8", errors="replace"))
                status_code = int(match.group(1)) if match else 500

                # Read response headers
                resp_headers_lines = []
                content_length = None
                is_chunked = False

                while True:
                    line = await upstream_reader.readline()
                    if not line or line == b"\r\n":
                        break
                    resp_headers_lines.append(line)
                    lower_line = line.lower()
                    if lower_line.startswith(b"content-length:"):
                        content_length = int(line.split(b":", 1)[1].strip())
                    elif lower_line.startswith(b"transfer-encoding:") and b"chunked" in lower_line:
                        is_chunked = True

                # Check for 429 Quota Exceeded (RESOURCE_EXHAUSTED)
                if status_code == 429 and active_acc:
                    error_payload = b""
                    if content_length is not None:
                        error_payload = await upstream_reader.readexactly(content_length)
                    elif is_chunked:
                        error_payload = await self._read_chunked_body(upstream_reader)

                    logger.warning(
                        "[Proxy] [!] 429 Quota Exceeded on %s. Auto-rotating to next account...",
                        active_acc.email,
                    )
                    # Close upstream connection before retry
                    upstream_writer.close()
                    await upstream_writer.wait_closed()

                    # Put exhausted account on 4h cooldown and rotate to next healthy account
                    ok, rot_msg = self.rotation_service.set_cooldown(hours=4.0)
                    if not ok:
                        logger.error("[Proxy] [x] All accounts exhausted: %s", rot_msg)
                        client_writer.write(status_line + b"".join(resp_headers_lines) + b"\r\n" + error_payload)
                        await client_writer.drain()
                        return
                    continue

                # Stream response headers and body directly back to client
                client_writer.write(status_line + b"".join(resp_headers_lines) + b"\r\n")
                await client_writer.drain()

                while True:
                    chunk = await upstream_reader.read(16384)
                    if not chunk:
                        break
                    client_writer.write(chunk)
                    await client_writer.drain()

                return

            except Exception as e:
                logger.error("[Proxy] [x] Upstream request error (attempt %d): %s", attempt, e)
                if attempt >= max_retries:
                    err_body = f'{{"error": {{"code": 502, "message": "Betteragy proxy upstream error: {e}"}}}}'
                    resp = (
                        f"HTTP/1.1 502 Bad Gateway\r\n"
                        f"Content-Type: application/json\r\n"
                        f"Content-Length: {len(err_body)}\r\n\r\n{err_body}"
                    )
                    client_writer.write(resp.encode("utf-8"))
                    await client_writer.drain()
                    return
            finally:
                if upstream_writer and not upstream_writer.is_closing():
                    upstream_writer.close()

    async def _read_chunked_body(self, reader: asyncio.StreamReader) -> bytes:
        """Read full chunked HTTP body until end chunk."""
        chunks = []
        while True:
            size_line = await reader.readline()
            if not size_line:
                break
            size_str = size_line.split(b";")[0].strip()
            chunk_size = int(size_str, 16)
            if chunk_size == 0:
                await reader.readline()  # read trailing CRLF
                break
            chunk_data = await reader.readexactly(chunk_size)
            await reader.readline()  # read CRLF
            chunks.append(chunk_data)
        return b"".join(chunks)
