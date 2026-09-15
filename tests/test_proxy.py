"""Unit and integration tests for Betteragy local proxy server and interceptor."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from betteragy.core.models import AccountRecord
from betteragy.proxy.daemon import is_healthy, is_proxy_running
from betteragy.proxy.interceptor import ProxyInterceptor
from betteragy.proxy.server import BetteragyProxyServer
from betteragy.services.cert_service import CertService


@pytest.mark.asyncio
async def test_proxy_server_health_and_status(tmp_path):
    """Verify /health and /status endpoints return JSON status ok."""
    cert_svc = CertService(certs_dir=tmp_path)
    mock_acc_svc = MagicMock()
    mock_acc = AccountRecord(email="active@example.com", refresh_token="dummy")
    mock_acc_svc.get_active_account.return_value = mock_acc
    interceptor = ProxyInterceptor(account_service=mock_acc_svc)

    server = BetteragyProxyServer(
        host="127.0.0.1",
        port=0,
        interceptor=interceptor,
        cert_service=cert_svc,
    )
    await server.start()
    port = server._server.sockets[0].getsockname()[1]

    try:
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        writer.write(b"GET /health HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n")
        await writer.drain()

        resp_line = await reader.readline()
        assert b"200 OK" in resp_line

        # Read until body
        while True:
            line = await reader.readline()
            if not line or line == b"\r\n":
                break

        body = await reader.readline()
        data = json.loads(body.decode("utf-8"))
        assert data["status"] == "ok"
        assert data["active_account"] == "active@example.com"
        writer.close()
        await writer.wait_closed()
    finally:
        await server.stop()


@pytest.mark.asyncio
async def test_interceptor_token_injection():
    """Verify interceptor dynamically injects active account Bearer token."""
    mock_acc_svc = MagicMock()
    mock_rot_svc = MagicMock()
    acc = AccountRecord(email="bot@example.com", refresh_token="rf123")
    mock_acc_svc.get_active_account.return_value = acc
    mock_acc_svc.ensure_valid_access_token.return_value = "new_access_token_xyz"

    interceptor = ProxyInterceptor(account_service=mock_acc_svc, rotation_service=mock_rot_svc)

    mock_upstream_reader = AsyncMock()
    mock_upstream_reader.readline.side_effect = [
        b"HTTP/1.1 200 OK\r\n",
        b"Content-Length: 2\r\n",
        b"\r\n",
    ]
    mock_upstream_reader.read.side_effect = [b"OK", b""]

    mock_upstream_writer = MagicMock()
    mock_upstream_writer.drain = AsyncMock()
    mock_upstream_writer.wait_closed = AsyncMock()

    mock_client_writer = MagicMock()
    mock_client_writer.drain = AsyncMock()

    with patch("asyncio.open_connection", return_value=(mock_upstream_reader, mock_upstream_writer)):
        await interceptor.forward_request(
            method="POST",
            path="/v1internal:generateCode",
            headers={"Authorization": "Bearer stale_token", "User-Agent": "agy-test"},
            body=b"{}",
            upstream_host="cloudcode-pa.googleapis.com",
            upstream_port=443,
            client_writer=mock_client_writer,
        )

    sent_data = mock_upstream_writer.write.call_args_list[0][0][0].decode("utf-8")
    assert "Authorization: Bearer new_access_token_xyz" in sent_data
    assert "Authorization: Bearer stale_token" not in sent_data


@pytest.mark.asyncio
async def test_interceptor_auto_rotation_on_429():
    """Verify 429 Quota Exceeded sets 4h cooldown, rotates account, and retries."""
    mock_acc_svc = MagicMock()
    mock_rot_svc = MagicMock()

    acc1 = AccountRecord(email="acc1@example.com", refresh_token="rf1")
    acc2 = AccountRecord(email="acc2@example.com", refresh_token="rf2")

    mock_acc_svc.get_active_account.side_effect = [acc1, acc2]
    mock_acc_svc.ensure_valid_access_token.side_effect = ["token1", "token2"]
    mock_rot_svc.set_cooldown.return_value = (True, "Switched to acc2")

    interceptor = ProxyInterceptor(account_service=mock_acc_svc, rotation_service=mock_rot_svc)

    reader_429 = AsyncMock()
    reader_429.readline.side_effect = [
        b"HTTP/1.1 429 Too Many Requests\r\n",
        b"Content-Length: 15\r\n",
        b"\r\n",
    ]
    reader_429.readexactly.return_value = b'{"error": "429"}'
    writer_429 = MagicMock()
    writer_429.drain = AsyncMock()
    writer_429.wait_closed = AsyncMock()

    reader_200 = AsyncMock()
    reader_200.readline.side_effect = [
        b"HTTP/1.1 200 OK\r\n",
        b"Content-Length: 2\r\n",
        b"\r\n",
    ]
    reader_200.read.side_effect = [b"OK", b""]
    writer_200 = MagicMock()
    writer_200.drain = AsyncMock()
    writer_200.wait_closed = AsyncMock()

    mock_client_writer = MagicMock()
    mock_client_writer.drain = AsyncMock()

    with patch("asyncio.open_connection", side_effect=[(reader_429, writer_429), (reader_200, writer_200)]):
        await interceptor.forward_request(
            method="POST",
            path="/v1internal:generateCode",
            headers={},
            body=b"{}",
            upstream_host="cloudcode-pa.googleapis.com",
            upstream_port=443,
            client_writer=mock_client_writer,
        )

    mock_rot_svc.set_cooldown.assert_called_once_with(hours=4.0)

    written_to_client = b"".join(call[0][0] for call in mock_client_writer.write.call_args_list)
    assert b"HTTP/1.1 200 OK" in written_to_client
    assert b"OK" in written_to_client


def test_daemon_health_and_status():
    """Verify is_healthy returns False when port is closed."""
    assert is_healthy("127.0.0.1", 59999) is False
    assert is_proxy_running("127.0.0.1", 59999) is False
