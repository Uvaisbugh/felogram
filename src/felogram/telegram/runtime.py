from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from queue import Empty, Queue
from uuid import uuid4

from felogram.telegram.transport import JsonObject, TdTransport

LOGGER = logging.getLogger(__name__)


class RuntimeEventKind(StrEnum):
    STARTING = "starting"
    VERSION = "version"
    AUTHORIZATION = "authorization"
    STATUS = "status"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    RESPONSE = "response"
    UPDATE = "update"


@dataclass(frozen=True, slots=True)
class RuntimeEvent:
    kind: RuntimeEventKind
    message: str
    data: JsonObject | None = None


@dataclass(frozen=True, slots=True)
class RuntimeCommand:
    operation: str
    request: JsonObject = field(repr=False)


class TdRuntime:
    """Own one TDLib client and its ordered receive loop."""

    def __init__(
        self,
        transport: TdTransport,
        *,
        receive_timeout: float = 0.1,
        close_timeout: float = 5.0,
    ) -> None:
        self._transport = transport
        self._receive_timeout = receive_timeout
        self._close_timeout = close_timeout

    def run(
        self,
        stop_requested: threading.Event,
        emit: Callable[[RuntimeEvent], None],
        commands: Queue[RuntimeCommand] | None = None,
    ) -> None:
        client_id: int | None = None
        close_sent = False
        close_deadline: float | None = None
        closed = False
        version_request_id = f"felogram-version-{uuid4()}"
        command_queue: Queue[RuntimeCommand] = commands or Queue()
        pending_commands: dict[str, str] = {}

        try:
            emit(RuntimeEvent(RuntimeEventKind.STARTING, "Loading TDLib..."))
            self._transport.execute({"@type": "setLogVerbosityLevel", "new_verbosity_level": 1})
            client_id = self._transport.create_client_id()
            self._transport.send(
                client_id,
                {"@type": "getOption", "name": "version", "@extra": version_request_id},
            )
            LOGGER.info("TDLib client created")

            while not closed:
                if stop_requested.is_set() and not close_sent:
                    emit(RuntimeEvent(RuntimeEventKind.STOPPING, "Closing TDLib..."))
                    self._transport.send(client_id, {"@type": "close"})
                    close_sent = True
                    close_deadline = time.monotonic() + self._close_timeout
                elif not close_sent:
                    self._drain_commands(client_id, command_queue, pending_commands)

                response = self._transport.receive(self._receive_timeout)
                if response is not None:
                    closed = self._handle_response(
                        response, version_request_id, pending_commands, emit
                    )

                if (
                    close_sent
                    and not closed
                    and close_deadline is not None
                    and time.monotonic() >= close_deadline
                ):
                    raise TimeoutError("TDLib did not reach authorizationStateClosed in time")
        except Exception as exc:
            LOGGER.exception("TDLib runtime failed: %s", type(exc).__name__)
            emit(RuntimeEvent(RuntimeEventKind.ERROR, f"TDLib error: {exc}"))
        finally:
            if client_id is None:
                emit(RuntimeEvent(RuntimeEventKind.STOPPED, "TDLib did not start"))
            elif closed:
                emit(RuntimeEvent(RuntimeEventKind.STOPPED, "TDLib closed cleanly"))
            else:
                emit(RuntimeEvent(RuntimeEventKind.STOPPED, "TDLib worker stopped"))

    def _drain_commands(
        self,
        client_id: int,
        commands: Queue[RuntimeCommand],
        pending_commands: dict[str, str],
    ) -> None:
        while True:
            try:
                command = commands.get_nowait()
            except Empty:
                return

            request_id = f"felogram-command-{uuid4()}"
            request = dict(command.request)
            request["@extra"] = request_id
            pending_commands[request_id] = command.operation
            self._transport.send(client_id, request)

    @staticmethod
    def _handle_response(
        response: JsonObject,
        version_request_id: str,
        pending_commands: dict[str, str],
        emit: Callable[[RuntimeEvent], None],
    ) -> bool:
        response_type = response.get("@type")
        response_extra = response.get("@extra")

        if response_extra == version_request_id:
            if response_type == "optionValueString" and isinstance(response.get("value"), str):
                emit(RuntimeEvent(RuntimeEventKind.VERSION, f"TDLib {response['value']}"))
            elif response_type == "error":
                emit(RuntimeEvent(RuntimeEventKind.ERROR, "TDLib version request failed"))

        if isinstance(response_extra, str) and response_extra in pending_commands:
            operation = pending_commands.pop(response_extra)
            emit(RuntimeEvent(RuntimeEventKind.RESPONSE, operation, response))
            if response_type == "error":
                error_message = response.get("message")
                error_code = response.get("code")
                detail = error_message if isinstance(error_message, str) else "Unknown TDLib error"
                if isinstance(error_code, int):
                    detail = f"{detail} (code {error_code})"
                emit(RuntimeEvent(RuntimeEventKind.ERROR, f"{operation} failed: {detail}"))
            else:
                emit(RuntimeEvent(RuntimeEventKind.STATUS, f"{operation} accepted"))

        if response_type != "updateAuthorizationState":
            if isinstance(response_type, str) and response_type.startswith("update"):
                emit(RuntimeEvent(RuntimeEventKind.UPDATE, response_type, response))
            return False

        state = response.get("authorization_state")
        if not isinstance(state, dict):
            emit(
                RuntimeEvent(
                    RuntimeEventKind.ERROR, "TDLib returned an invalid authorization state"
                )
            )
            return False

        state_type = state.get("@type")
        if not isinstance(state_type, str):
            emit(RuntimeEvent(RuntimeEventKind.ERROR, "TDLib authorization state has no type"))
            return False

        emit(RuntimeEvent(RuntimeEventKind.AUTHORIZATION, state_type, state))
        return state_type == "authorizationStateClosed"
