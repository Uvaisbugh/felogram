from __future__ import annotations

import base64
from pathlib import Path

import pytest

import felogram.security as security
from felogram.application.auth import AppPaths, AuthInputError, AuthRequestFactory
from felogram.security import WindowsDpapiSecretStore


class FakeSecretStore:
    def __init__(self, secret: bytes) -> None:
        self.secret = secret

    def get_or_create(self, *, length: int = 32) -> bytes:
        assert length == 32
        return self.secret


def test_configure_builds_current_tdlib_parameters(tmp_path: Path) -> None:
    secret = b"a" * 32
    factory = AuthRequestFactory(AppPaths(tmp_path), FakeSecretStore(secret))

    command = factory.configure("12345", "0123456789abcdef0123456789ABCDEF")

    assert command.operation == "Configure TDLib"
    assert command.request["@type"] == "setTdlibParameters"
    assert command.request["api_id"] == 12345
    assert command.request["api_hash"] == "0123456789abcdef0123456789abcdef"
    assert command.request["database_encryption_key"] == base64.b64encode(secret).decode("ascii")
    assert command.request["database_directory"] == str(tmp_path / "tdlib" / "database")
    assert "api_hash" not in repr(command)


@pytest.mark.parametrize(
    ("api_id", "api_hash"),
    [("", "0" * 32), ("0", "0" * 32), ("123", "not-a-hash")],
)
def test_configure_rejects_invalid_credentials(tmp_path: Path, api_id: str, api_hash: str) -> None:
    factory = AuthRequestFactory(AppPaths(tmp_path), FakeSecretStore(b"a" * 32))

    with pytest.raises(AuthInputError):
        factory.configure(api_id, api_hash)


def test_authentication_requests_match_tdlib_schema() -> None:
    assert AuthRequestFactory.phone("+91 98765-43210").request == {
        "@type": "setAuthenticationPhoneNumber",
        "phone_number": "+919876543210",
    }
    assert AuthRequestFactory.code(" 12345 ").request == {
        "@type": "checkAuthenticationCode",
        "code": "12345",
    }
    assert AuthRequestFactory.email_code("67890").request == {
        "@type": "checkAuthenticationEmailCode",
        "code": {"@type": "emailAddressAuthenticationCode", "code": "67890"},
    }


def test_phone_number_requires_international_format() -> None:
    with pytest.raises(AuthInputError):
        AuthRequestFactory.phone("9876543210")


def test_dpapi_secret_store_round_trip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    prefix = b"protected:"

    def protect(data: bytes, *_args: object) -> bytes:
        return prefix + data[::-1]

    def unprotect(data: bytes, *_args: object) -> tuple[str, bytes]:
        return "Felogram TDLib database key", data.removeprefix(prefix)[::-1]

    monkeypatch.setattr(security.win32crypt, "CryptProtectData", protect)
    monkeypatch.setattr(security.win32crypt, "CryptUnprotectData", unprotect)
    path = tmp_path / "database-key.dpapi"
    first = WindowsDpapiSecretStore(path).get_or_create()
    second = WindowsDpapiSecretStore(path).get_or_create()

    assert len(first) == 32
    assert second == first
    assert path.read_bytes() != first


@pytest.mark.native
def test_remembered_credentials_are_protected_and_can_be_forgotten(tmp_path: Path) -> None:
    factory = AuthRequestFactory(AppPaths(tmp_path), FakeSecretStore(b"a" * 32))
    assert factory.load_api_credentials() is None
    api_hash = "0123456789abcdef0123456789abcdef"
    factory.remember_api_credentials("12345", api_hash)
    assert api_hash.encode() not in (tmp_path / "secrets" / "telegram-api.dpapi").read_bytes()
    credentials = factory.load_api_credentials()
    assert credentials is not None
    assert credentials.api_id == 12345
    assert credentials.api_hash == api_hash
    factory.forget_api_credentials()
    assert factory.load_api_credentials() is None
