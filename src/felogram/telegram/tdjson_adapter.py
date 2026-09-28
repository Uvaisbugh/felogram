from __future__ import annotations

import importlib
import json
from collections.abc import Mapping
from types import ModuleType
from typing import cast

from felogram.telegram.transport import JsonObject, JsonValue


class TdjsonUnavailableError(RuntimeError):
    """Raised when the native TDLib binding cannot be imported."""


class TdjsonProtocolError(RuntimeError):
    """Raised when the native binding returns an invalid JSON object."""


def decode_tdjson(payload: bytes | str | None) -> JsonObject | None:
    if payload is None:
        return None
    try:
        decoded = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TdjsonProtocolError("TDLib returned malformed JSON") from exc
    if not isinstance(decoded, dict):
        raise TdjsonProtocolError("TDLib returned JSON that is not an object")
    if not all(isinstance(key, str) for key in decoded):
        raise TdjsonProtocolError("TDLib returned an object with a non-string key")
    return cast(JsonObject, decoded)


class TdjsonTransport:
    """Encode Python objects for the third-party tdjson native binding."""

    def __init__(self, module: ModuleType | None = None) -> None:
        if module is not None:
            self._module = module
            return
        try:
            self._module = importlib.import_module("tdjson")
        except (ImportError, OSError) as exc:
            raise TdjsonUnavailableError(
                "TDLib could not be loaded. Run 'uv sync' and verify the tdjson Windows wheel."
            ) from exc

    def create_client_id(self) -> int:
        return int(self._module.td_create_client_id())

    def send(self, client_id: int, request: Mapping[str, JsonValue]) -> None:
        self._module.td_send(client_id, self._encode(request))

    def receive(self, timeout: float) -> JsonObject | None:
        return decode_tdjson(self._module.td_receive(timeout))

    def execute(self, request: Mapping[str, JsonValue]) -> JsonObject | None:
        return decode_tdjson(self._module.td_execute(self._encode(request)))

    @staticmethod
    def _encode(request: Mapping[str, JsonValue]) -> bytes:
        return json.dumps(request, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
