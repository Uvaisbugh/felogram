from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]
type JsonObject = dict[str, JsonValue]


class TdTransport(Protocol):
    """Small boundary around the modern TDLib JSON interface."""

    def create_client_id(self) -> int: ...

    def send(self, client_id: int, request: Mapping[str, JsonValue]) -> None: ...

    def receive(self, timeout: float) -> JsonObject | None: ...

    def execute(self, request: Mapping[str, JsonValue]) -> JsonObject | None: ...
