"""Keyring adapter for Antigravity (service="gemini", account="antigravity")."""

import base64
import json
import subprocess
from typing import Optional

from ..core.constants import IS_LINUX, IS_MAC, KEYRING_ACCOUNT, KEYRING_PREFIX, KEYRING_SERVICE


class KeyringAdapter:
    """Read and write go-keyring-base64 credentials for Antigravity."""

    @staticmethod
    def encode_payload(access_token: str, refresh_token: str, expiry: str) -> str:
        """Wrap tokens in the Antigravity go-keyring-base64 JSON envelope."""
        payload = {
            "token": {
                "access_token": access_token,
                "token_type": "Bearer",
                "refresh_token": refresh_token,
                "expiry": expiry,
            },
            "auth_method": "consumer",
        }
        json_bytes = json.dumps(payload).encode("utf-8")
        b64_str = base64.b64encode(json_bytes).decode("ascii")
        return f"{KEYRING_PREFIX}{b64_str}"

    @staticmethod
    def decode_payload(envelope_str: str) -> Optional[dict]:
        """Decode a go-keyring-base64 envelope string into dictionary."""
        envelope_str = envelope_str.strip()
        if not envelope_str.startswith(KEYRING_PREFIX):
            return None
        b64_part = envelope_str[len(KEYRING_PREFIX) :]
        try:
            raw_json = base64.b64decode(b64_part).decode("utf-8")
            return json.loads(raw_json)
        except Exception:
            return None

    @classmethod
    def read_active_credential(cls) -> Optional[dict]:
        """Read the currently active credentials from the system keyring."""
        raw_output = None
        if IS_MAC:
            try:
                cmd = [
                    "security",
                    "find-generic-password",
                    "-a",
                    KEYRING_ACCOUNT,
                    "-s",
                    KEYRING_SERVICE,
                    "-w",
                ]
                res = subprocess.run(cmd, capture_output=True, text=True, check=True)
                raw_output = res.stdout.strip()
            except Exception:
                return None
        elif IS_LINUX:
            try:
                cmd = [
                    "secret-tool",
                    "lookup",
                    "service",
                    KEYRING_SERVICE,
                    "username",
                    KEYRING_ACCOUNT,
                ]
                res = subprocess.run(cmd, capture_output=True, text=True, check=True)
                raw_output = res.stdout.strip()
            except Exception:
                return None

        if not raw_output:
            return None

        return cls.decode_payload(raw_output)

    @classmethod
    def write_credential(cls, access_token: str, refresh_token: str, expiry: str) -> bool:
        """Inject updated go-keyring-base64 credentials into system keyring."""
        envelope = cls.encode_payload(access_token, refresh_token, expiry)

        if IS_MAC:
            try:
                cmd = [
                    "security",
                    "add-generic-password",
                    "-a",
                    KEYRING_ACCOUNT,
                    "-s",
                    KEYRING_SERVICE,
                    "-w",
                    envelope,
                    "-U",
                ]
                subprocess.run(cmd, capture_output=True, text=True, check=True)
                return True
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"macOS Keychain write failed: {e.stderr.strip() or e}")
        elif IS_LINUX:
            try:
                cmd = [
                    "secret-tool",
                    "store",
                    "--label=gemini",
                    "service",
                    KEYRING_SERVICE,
                    "username",
                    KEYRING_ACCOUNT,
                ]
                proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, text=True)
                proc.communicate(input=envelope)
                if proc.returncode != 0:
                    raise RuntimeError("secret-tool store returned non-zero exit code")
                return True
            except Exception as e:
                raise RuntimeError(f"Linux Secret Service write failed: {e}")
        else:
            raise NotImplementedError("Windows Credential Manager is not currently supported.")
