"""Unit tests for CertService (Root CA and SSL certificate generation)."""

import ssl
from pathlib import Path

from betteragy.services.cert_service import CertService


def test_cert_generation(tmp_path: Path):
    """Test generating Root CA and server certificates from scratch."""
    service = CertService(certs_dir=tmp_path)
    ca_crt, server_crt, server_key = service.ensure_certs()

    assert ca_crt.exists()
    assert service.ca_key.exists()
    assert server_crt.exists()
    assert server_key.exists()

    ca_content = ca_crt.read_text()
    assert "-----BEGIN CERTIFICATE-----" in ca_content
    assert "-----END CERTIFICATE-----" in ca_content

    server_content = server_crt.read_text()
    assert "-----BEGIN CERTIFICATE-----" in server_content
    assert "-----END CERTIFICATE-----" in server_content


def test_cert_idempotency(tmp_path: Path):
    """Test that existing valid certificates are reused without regeneration."""
    service = CertService(certs_dir=tmp_path)
    ca_crt1, server_crt1, _ = service.ensure_certs()
    content1 = ca_crt1.read_text()

    ca_crt2, server_crt2, _ = service.ensure_certs()
    content2 = ca_crt2.read_text()

    assert content1 == content2
    assert server_crt1.exists()


def test_server_ssl_context(tmp_path: Path):
    """Test SSLContext creation with generated certificates."""
    service = CertService(certs_dir=tmp_path)
    ctx = service.get_server_ssl_context()
    assert isinstance(ctx, ssl.SSLContext)
    assert ctx.protocol == ssl.PROTOCOL_TLS_SERVER


def test_ca_cert_path(tmp_path: Path):
    """Test retrieving the CA certificate bundle path."""
    service = CertService(certs_dir=tmp_path)
    ca_path = service.get_ca_cert_path()
    assert ca_path == tmp_path / "ca_bundle.crt"
    assert ca_path.exists()
    assert service.ca_crt.exists()
