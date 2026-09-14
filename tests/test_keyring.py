"""Unit tests for keyring adapter encoding and decoding."""

import pytest
from betteragy.services.keyring_adapter import KeyringAdapter


def test_keyring_encode_decode_roundtrip():
    access_token = "ya29.sample-access-token"
    refresh_token = "1//sample-refresh-token"
    expiry = "2026-09-14T22:00:00+00:00"

    envelope = KeyringAdapter.encode_payload(access_token, refresh_token, expiry)
    assert envelope.startswith("go-keyring-base64:")

    decoded = KeyringAdapter.decode_payload(envelope)
    assert decoded is not None
    assert decoded["auth_method"] == "consumer"
    assert "token" in decoded

    token_info = decoded["token"]
    assert token_info["access_token"] == access_token
    assert token_info["refresh_token"] == refresh_token
    assert token_info["expiry"] == expiry
    assert token_info["token_type"] == "Bearer"


def test_keyring_decode_invalid_envelope():
    assert KeyringAdapter.decode_payload("invalid-prefix") is None
    assert KeyringAdapter.decode_payload("go-keyring-base64:!!!not-valid-base64") is None
