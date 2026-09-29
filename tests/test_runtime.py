from __future__ import annotations

import threading
from collections import deque
from collections.abc import Mapping
from queue import Queue

from felogram.telegram.runtime import RuntimeCommand, RuntimeEvent, RuntimeEventKind, TdRuntime
from felogram.telegram.transport import JsonObject, JsonValue


class FakeTransport:
    def __init__(self) -> None:
        self.responses: deque[JsonObject] = deque()
        self.sent: list[tuple[int, Mapping[str, JsonValue]]] = []

    def create_client_id(self) -> int:
        return 42

    def send(self, client_id: int, request: Mapping[str, JsonValue]) -> None:
        self.sent.append((client_id, request))
        request_type = request["@type"]
        if request_type == "getOption":
            self.responses.extend(
                [
                    {
                        "@type": "optionValueString",
                        "value": "1.8.test",
                        "@extra": request["@extra"],
                    },
                    {
                        "@type": "updateAuthorizationState",
                        "authorization_state": {"@type": "authorizationStateWaitTdlibParameters"},
                    },
                ]
            )
        elif request_type == "close":
            self.responses.append(
                {
                    "@type": "updateAuthorizationState",
                    "authorization_state": {"@type": "authorizationStateClosed"},
                }
            )
        elif request_type == "setAuthenticationPhoneNumber":
            self.responses.append(
                {
                    "@type": "error",
                    "code": 400,
                    "message": "PHONE_NUMBER_INVALID",
                    "@extra": request["@extra"],
                }
            )

    def receive(self, timeout: float) -> JsonObject | None:
        del timeout
        return self.responses.popleft() if self.responses else None

    def execute(self, request: Mapping[str, JsonValue]) -> JsonObject | None:
        del request
        return None


def test_runtime_reports_version_state_and_closes() -> None:
    transport = FakeTransport()
    runtime = TdRuntime(transport, receive_timeout=0.0, close_timeout=0.1)
    stop_requested = threading.Event()
    events: list[RuntimeEvent] = []

    def capture(event: RuntimeEvent) -> None:
        events.append(event)
        if event.message == "authorizationStateWaitTdlibParameters":
            stop_requested.set()

    runtime.run(stop_requested, capture)

    assert [request[1]["@type"] for request in transport.sent] == ["getOption", "close"]
    assert RuntimeEvent(RuntimeEventKind.VERSION, "TDLib 1.8.test") in events
    assert (
        RuntimeEvent(
            RuntimeEventKind.AUTHORIZATION,
            "authorizationStateWaitTdlibParameters",
            {"@type": "authorizationStateWaitTdlibParameters"},
        )
        in events
    )
    assert events[-1] == RuntimeEvent(RuntimeEventKind.STOPPED, "TDLib closed cleanly")


def test_runtime_reports_transport_failure() -> None:
    class FailingTransport(FakeTransport):
        def create_client_id(self) -> int:
            raise OSError("native library missing")

    events: list[RuntimeEvent] = []
    TdRuntime(FailingTransport()).run(threading.Event(), events.append)

    assert events[-2].kind == RuntimeEventKind.ERROR
    assert "native library missing" in events[-2].message
    assert events[-1] == RuntimeEvent(RuntimeEventKind.STOPPED, "TDLib did not start")


def test_runtime_routes_commands_and_reports_safe_errors() -> None:
    transport = FakeTransport()
    runtime = TdRuntime(transport, receive_timeout=0.0, close_timeout=0.1)
    stop_requested = threading.Event()
    events: list[RuntimeEvent] = []
    commands: Queue[RuntimeCommand] = Queue()
    phone_number = "+919876543210"
    commands.put(
        RuntimeCommand(
            "Submit phone number",
            {"@type": "setAuthenticationPhoneNumber", "phone_number": phone_number},
        )
    )

    def capture(event: RuntimeEvent) -> None:
        events.append(event)
        if event.kind == RuntimeEventKind.ERROR:
            stop_requested.set()

    runtime.run(stop_requested, capture, commands)

    request_types = [request[1]["@type"] for request in transport.sent]
    assert request_types == ["getOption", "setAuthenticationPhoneNumber", "close"]
    error = next(event for event in events if event.kind == RuntimeEventKind.ERROR)
    assert error.message == "Submit phone number failed: PHONE_NUMBER_INVALID (code 400)"
    assert phone_number not in error.message
