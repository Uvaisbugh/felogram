from __future__ import annotations

import os
import secrets
from pathlib import Path
from typing import Protocol

import pywintypes
import win32crypt

CRYPTPROTECT_UI_FORBIDDEN = 0x01


class SecretStoreError(RuntimeError):
    """Raised when Felogram cannot protect or recover a local secret."""


class SecretStore(Protocol):
    def get_or_create(self, *, length: int = 32) -> bytes: ...


class WindowsDpapiSecretStore:
    """Persist a secret encrypted for the current Windows user."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def get_or_create(self, *, length: int = 32) -> bytes:
        try:
            if self._path.exists():
                return self._unprotect(self._path.read_bytes())
        except OSError as exc:
            raise SecretStoreError("Felogram could not read the protected session key") from exc

        secret = secrets.token_bytes(length)
        protected = self._protect(secret)
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            temporary_path = self._path.with_suffix(f"{self._path.suffix}.tmp")
            temporary_path.write_bytes(protected)
            os.replace(temporary_path, self._path)
        except OSError as exc:
            raise SecretStoreError("Felogram could not save the protected session key") from exc
        return secret

    @staticmethod
    def _protect(secret: bytes) -> bytes:
        try:
            protected = win32crypt.CryptProtectData(
                secret,
                "Felogram TDLib database key",
                None,
                None,
                None,
                CRYPTPROTECT_UI_FORBIDDEN,
            )
        except pywintypes.error as exc:
            raise SecretStoreError("Windows could not protect the session key") from exc
        return bytes(protected)

    @staticmethod
    def _unprotect(protected: bytes) -> bytes:
        try:
            _, secret = win32crypt.CryptUnprotectData(
                protected,
                None,
                None,
                None,
                CRYPTPROTECT_UI_FORBIDDEN,
            )
        except pywintypes.error as exc:
            raise SecretStoreError("Windows could not unlock the session key") from exc
        return bytes(secret)
