"""Local TLS certificate generator and manager for Betteragy MITM Proxy."""

import os
import shutil
import ssl
import subprocess
import tempfile
from pathlib import Path
from typing import Tuple

from ..core.constants import CONFIG_DIR

DEFAULT_CERTS_DIR = CONFIG_DIR / "certs"


class CertService:
    """Manages creation and loading of local CA and server certificates."""

    def __init__(self, certs_dir: Path = DEFAULT_CERTS_DIR):
        self.certs_dir = Path(certs_dir)
        self.ca_key = self.certs_dir / "ca.key"
        self.ca_crt = self.certs_dir / "ca.crt"
        self.server_key = self.certs_dir / "server.key"
        self.server_crt = self.certs_dir / "server.crt"

    def ensure_certs(self) -> Tuple[Path, Path, Path]:
        """Ensure CA and server certificates exist, generating them if needed."""
        self.certs_dir.mkdir(parents=True, exist_ok=True)

        if self.ca_crt.exists() and self.server_crt.exists() and self.server_key.exists():
            return self.ca_crt, self.server_crt, self.server_key

        openssl_bin = shutil.which("openssl")
        if not openssl_bin:
            raise RuntimeError("OpenSSL CLI binary not found in system PATH.")

        # 1. Generate Root CA key and certificate
        if not (self.ca_key.exists() and self.ca_crt.exists()):
            subprocess.run(
                [
                    openssl_bin,
                    "req",
                    "-x509",
                    "-newkey",
                    "rsa:2048",
                    "-keyout",
                    str(self.ca_key),
                    "-out",
                    str(self.ca_crt),
                    "-days",
                    "3650",
                    "-nodes",
                    "-subj",
                    "/CN=Betteragy Local Proxy CA/O=Betteragy/OU=Security",
                ],
                check=True,
                capture_output=True,
            )
            # Secure private key file permissions (0600)
            os.chmod(self.ca_key, 0o600)

        # 2. Generate Server key and CSR
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            server_csr = tmp_path / "server.csr"
            ext_file = tmp_path / "server.ext"

            ext_file.write_text(
                "basicConstraints=CA:FALSE\n"
                "keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment\n"
                "subjectAltName = @alt_names\n\n"
                "[alt_names]\n"
                "DNS.1 = *.googleapis.com\n"
                "DNS.2 = daily-cloudcode-pa.googleapis.com\n"
                "DNS.3 = cloudcode-pa.googleapis.com\n"
                "DNS.4 = localhost\n"
                "IP.1 = 127.0.0.1\n",
                encoding="utf-8",
            )

            subprocess.run(
                [
                    openssl_bin,
                    "req",
                    "-newkey",
                    "rsa:2048",
                    "-keyout",
                    str(self.server_key),
                    "-out",
                    str(server_csr),
                    "-nodes",
                    "-subj",
                    "/CN=*.googleapis.com/O=Betteragy Local Server",
                ],
                check=True,
                capture_output=True,
            )
            os.chmod(self.server_key, 0o600)

            # 3. Sign server certificate with Root CA
            subprocess.run(
                [
                    openssl_bin,
                    "x509",
                    "-req",
                    "-in",
                    str(server_csr),
                    "-CA",
                    str(self.ca_crt),
                    "-CAkey",
                    str(self.ca_key),
                    "-CAcreateserial",
                    "-out",
                    str(self.server_crt),
                    "-days",
                    "1825",
                    "-extfile",
                    str(ext_file),
                ],
                check=True,
                capture_output=True,
            )

        return self.ca_crt, self.server_crt, self.server_key

    def get_server_ssl_context(self) -> ssl.SSLContext:
        """Create and return a configured SSLContext for TLS interception."""
        self.ensure_certs()
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(certfile=self.server_crt, keyfile=self.server_key)
        # Force HTTP/1.1 for reliable SSE streaming support
        ctx.set_alpn_protocols(["http/1.1"])
        return ctx

    def get_ca_cert_path(self) -> Path:
        """Return path to Root CA certificate, ensuring it exists."""
        self.ensure_certs()
        return self.ca_crt

