"""Proxy interceptor: token swapping, 429 quota interception, and auto-rotation."""

import asyncio
import logging
import re
from typing import Dict, Optional

from ..services.account_service import AccountService
from ..services.rotation_service import RotationService
from .stream_utils import read_chunked_payload, stream_chunked_response, stream_fixed_response

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
    ) -> bool:
        """Forward request to upstream with token swapping. Returns True if client conn should close."""
        max_retries, attempt = 3, 0
        client_wants_close = headers.get("connection", "").strip().lower() == "close"
        headers_sent = False

        cleaned_headers = {
            k: v for k, v in headers.items()
            if k.lower() not in (
                "connection", "keep-alive", "proxy-authenticate",
                "proxy-authorization", "transfer-encoding", "content-length", "expect",
            )
        }
        cleaned_headers["Host"] = upstream_host
        cleaned_headers["Connection"] = "close"
        if method.upper() in ("POST", "PUT", "PATCH") or len(body) > 0:
            cleaned_headers["Content-Length"] = str(len(body))

        while attempt < max_retries:
            attempt += 1
            active_acc = self.account_service.get_active_account()
            if active_acc:
                try:
                    token = await asyncio.to_thread(self.account_service.ensure_valid_access_token, active_acc)
                    cleaned_headers["Authorization"] = f"Bearer {token}"
                    logger.info("[Proxy] [~] Injected token for active account: %s", active_acc.email)
                except Exception as e:
                    logger.warning("[Proxy] [!] Failed to refresh token for %s: %s", active_acc.email, e)

            upstream_reader, upstream_writer = None, None
            try:
                upstream_reader, upstream_writer = await asyncio.wait_for(
                    asyncio.open_connection(upstream_host, upstream_port, ssl=True), timeout=10.0,
                )
                req_line = f"{method} {path} HTTP/1.1\r\n"
                headers_data = "".join(f"{k}: {v}\r\n" for k, v in cleaned_headers.items())
                upstream_writer.write((req_line + headers_data + "\r\n").encode("utf-8") + body)
                await upstream_writer.drain()

                # Read status line, skipping informational 100 Continue
                status_code, status_line = 500, b""
                while True:
                    status_line = await upstream_reader.readline()
                    if not status_line:
                        raise IOError("Empty response from upstream")
                    match = re.match(r"^HTTP/\d\.\d\s+(\d+)", status_line.decode("utf-8", errors="replace"))
                    status_code = int(match.group(1)) if match else 500
                    if status_code == 100:
                        while True:
                            info_l = await upstream_reader.readline()
                            if not info_l or info_l == b"\r\n":
                                break
                        continue
                    break

                resp_headers_lines, content_length, is_chunked = [], None, False
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

                # Check for 429 Quota Exceeded
                if status_code == 429 and active_acc:
                    error_payload = b""
                    if content_length is not None:
                        error_payload = await upstream_reader.readexactly(content_length)
                    elif is_chunked:
                        error_payload = await read_chunked_payload(upstream_reader)

                    logger.warning("[Proxy] [!] 429 Quota Exceeded on %s. Auto-rotating...", active_acc.email)
                    upstream_writer.close()
                    await upstream_writer.wait_closed()

                    ok, rot_msg = await asyncio.to_thread(self.rotation_service.set_cooldown, hours=4.0)
                    if not ok:
                        logger.error("[Proxy] [x] All accounts exhausted: %s", rot_msg)
                        client_writer.write(status_line + b"".join(resp_headers_lines) + b"\r\n" + error_payload)
                        await client_writer.drain()
                        return True
                    continue

                # Strip hop-by-hop headers from upstream and preserve client keep-alive
                out_headers = [
                    h for h in resp_headers_lines
                    if not h.lower().startswith((b"connection:", b"keep-alive:"))
                ]
                if client_wants_close:
                    out_headers.append(b"Connection: close\r\n")
                else:
                    out_headers.append(b"Connection: keep-alive\r\nKeep-Alive: timeout=60\r\n")

                client_writer.write(status_line + b"".join(out_headers) + b"\r\n")
                await client_writer.drain()
                headers_sent = True

                # Stream body based on HTTP framing
                if status_code in (204, 304) or (100 <= status_code < 200):
                    pass
                elif is_chunked:
                    await stream_chunked_response(upstream_reader, client_writer)
                elif content_length is not None:
                    await stream_fixed_response(upstream_reader, client_writer, content_length)
                else:
                    while True:
                        chunk = await upstream_reader.read(16384)
                        if not chunk:
                            break
                        client_writer.write(chunk)
                        await client_writer.drain()

                return client_wants_close

            except (ConnectionResetError, BrokenPipeError, asyncio.CancelledError):
                return True
            except Exception as e:
                logger.error("[Proxy] [x] Upstream request error (attempt %d): %s", attempt, e)
                if attempt >= max_retries and not headers_sent:
                    err_body = f'{{"error": {{"code": 502, "message": "Betteragy proxy upstream error: {e}"}}}}'
                    resp = (
                        f"HTTP/1.1 502 Bad Gateway\r\n"
                        f"Content-Type: application/json\r\n"
                        f"Content-Length: {len(err_body)}\r\n\r\n{err_body}"
                    )
                    try:
                        client_writer.write(resp.encode("utf-8"))
                        await client_writer.drain()
                    except Exception:
                        pass
                    return True
            finally:
                if upstream_writer and not upstream_writer.is_closing():
                    upstream_writer.close()
        return True
