from __future__ import annotations

import base64
import json
import os
import platform
import re
from dataclasses import dataclass, field
from pathlib import Path

from felogram import __version__
from felogram.security import SecretStore, WindowsDpapiSecretStore
from felogram.telegram.runtime import RuntimeCommand
from felogram.telegram.transport import JsonObject

API_HASH_PATTERN = re.compile(r"[0-9a-fA-F]{32}")
PHONE_SEPARATOR_PATTERN = re.compile(r"[\s()-]")
PHONE_PATTERN = re.compile(r"\+[1-9][0-9]{6,14}")


class AuthInputError(ValueError):
    """Raised when a user-provided authorization value is invalid."""


@dataclass(frozen=True, slots=True)
class TelegramApiCredentials:
    api_id: int
    api_hash: str = field(repr=False)

    @classmethod
    def parse(cls, api_id: str, api_hash: str) -> TelegramApiCredentials:
        try:
            parsed_id = int(api_id.strip())
        except ValueError as exc:
            raise AuthInputError("API ID must be a positive number") from exc
        if parsed_id <= 0:
            raise AuthInputError("API ID must be a positive number")

        normalized_hash = api_hash.strip()
        if API_HASH_PATTERN.fullmatch(normalized_hash) is None:
            raise AuthInputError("API hash must contain exactly 32 hexadecimal characters")
        return cls(api_id=parsed_id, api_hash=normalized_hash.lower())


@dataclass(frozen=True, slots=True)
class AppPaths:
    data_root: Path

    @classmethod
    def default(cls) -> AppPaths:
        local_app_data = os.environ.get("LOCALAPPDATA")
        root = Path(local_app_data) if local_app_data else Path.home() / "AppData" / "Local"
        return cls(root / "Felogram")

    @property
    def database_directory(self) -> Path:
        return self.data_root / "tdlib" / "database"

    @property
    def files_directory(self) -> Path:
        return self.data_root / "tdlib" / "files"

    @property
    def protected_key_path(self) -> Path:
        return self.data_root / "secrets" / "tdlib-database-key.dpapi"

    @property
    def api_credentials_path(self) -> Path:
        return self.data_root / "secrets" / "telegram-api.dpapi"


class AuthRequestFactory:
    """Validate input and build the narrow set of TDLib authorization requests."""

    def __init__(
        self,
        paths: AppPaths | None = None,
        secret_store: SecretStore | None = None,
    ) -> None:
        self._paths = paths or AppPaths.default()
        self._secret_store = secret_store or WindowsDpapiSecretStore(self._paths.protected_key_path)

    def load_api_credentials(self) -> TelegramApiCredentials | None:
        path = self._paths.api_credentials_path
        if not path.exists():
            return None
        payload = json.loads(WindowsDpapiSecretStore._unprotect(path.read_bytes()))
        if not isinstance(payload, dict):
            raise AuthInputError("Saved API credentials could not be read")
        return TelegramApiCredentials.parse(
            str(payload.get("api_id", "")), str(payload.get("api_hash", ""))
        )

    def remember_api_credentials(self, api_id: str, api_hash: str) -> None:
        credentials = TelegramApiCredentials.parse(api_id, api_hash)
        payload = json.dumps(
            {"api_id": credentials.api_id, "api_hash": credentials.api_hash}
        ).encode()
        protected = WindowsDpapiSecretStore._protect(payload)
        path = self._paths.api_credentials_path
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_bytes(protected)
        temporary.replace(path)

    def forget_api_credentials(self) -> None:
        self._paths.api_credentials_path.unlink(missing_ok=True)

    def configure(self, api_id: str, api_hash: str) -> RuntimeCommand:
        credentials = TelegramApiCredentials.parse(api_id, api_hash)
        encryption_key = base64.b64encode(self._secret_store.get_or_create()).decode("ascii")
        request: JsonObject = {
            "@type": "setTdlibParameters",
            "use_test_dc": False,
            "database_directory": str(self._paths.database_directory),
            "files_directory": str(self._paths.files_directory),
            "database_encryption_key": encryption_key,
            "use_file_database": True,
            "use_chat_info_database": True,
            "use_message_database": True,
            "use_secret_chats": True,
            "api_id": credentials.api_id,
            "api_hash": credentials.api_hash,
            "system_language_code": self._system_language_code(),
            "device_model": "Desktop",
            "system_version": platform.platform(),
            "application_version": __version__,
        }
        return RuntimeCommand("Configure TDLib", request)

    @staticmethod
    def phone(phone_number: str) -> RuntimeCommand:
        normalized = PHONE_SEPARATOR_PATTERN.sub("", phone_number.strip())
        if PHONE_PATTERN.fullmatch(normalized) is None:
            raise AuthInputError(
                "Enter a phone number in international format, such as +919876543210"
            )
        return RuntimeCommand(
            "Submit phone number",
            {"@type": "setAuthenticationPhoneNumber", "phone_number": normalized},
        )

    @staticmethod
    def code(code: str) -> RuntimeCommand:
        normalized = code.strip()
        if not normalized:
            raise AuthInputError("Enter the authentication code")
        return RuntimeCommand(
            "Check authentication code",
            {"@type": "checkAuthenticationCode", "code": normalized},
        )

    @staticmethod
    def password(password: str) -> RuntimeCommand:
        if not password:
            raise AuthInputError("Enter your two-step verification password")
        return RuntimeCommand(
            "Check two-step verification password",
            {"@type": "checkAuthenticationPassword", "password": password},
        )

    @staticmethod
    def email(email_address: str) -> RuntimeCommand:
        normalized = email_address.strip()
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise AuthInputError("Enter a valid email address")
        return RuntimeCommand(
            "Submit email address",
            {"@type": "setAuthenticationEmailAddress", "email_address": normalized},
        )

    @staticmethod
    def email_code(code: str) -> RuntimeCommand:
        normalized = code.strip()
        if not normalized:
            raise AuthInputError("Enter the email authentication code")
        return RuntimeCommand(
            "Check email authentication code",
            {
                "@type": "checkAuthenticationEmailCode",
                "code": {"@type": "emailAddressAuthenticationCode", "code": normalized},
            },
        )

    @staticmethod
    def registration(first_name: str, last_name: str) -> RuntimeCommand:
        first = first_name.strip()
        last = last_name.strip()
        if not 1 <= len(first) <= 64:
            raise AuthInputError("First name must contain 1 to 64 characters")
        if len(last) > 64:
            raise AuthInputError("Last name must contain at most 64 characters")
        return RuntimeCommand(
            "Register Telegram account",
            {
                "@type": "registerUser",
                "first_name": first,
                "last_name": last,
                "disable_notification": False,
            },
        )

    @staticmethod
    def _system_language_code() -> str:
        language = os.environ.get("LANG", "en-US").split(".", maxsplit=1)[0]
        return language.replace("_", "-") or "en-US"
