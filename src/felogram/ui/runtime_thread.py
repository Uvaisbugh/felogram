from __future__ import annotations

import threading
from collections.abc import Callable
from queue import Queue

from PySide6.QtCore import QObject, QThread, Signal

from felogram.telegram.runtime import RuntimeCommand, RuntimeEvent, RuntimeEventKind, TdRuntime


class TdRuntimeThread(QThread):
    """Run the blocking TDLib receive loop away from the UI thread."""

    event_received = Signal(object)

    def __init__(
        self, runtime_factory: Callable[[], TdRuntime], parent: QObject | None = None
    ) -> None:
        super().__init__(parent)
        self._runtime_factory = runtime_factory
        self._stop_requested = threading.Event()
        self._commands: Queue[RuntimeCommand] = Queue()
        self.setObjectName("TDLib runtime")

    def request_stop(self) -> None:
        self._stop_requested.set()

    def submit(self, command: RuntimeCommand) -> None:
        self._commands.put(command)

    def run(self) -> None:
        try:
            runtime = self._runtime_factory()
            runtime.run(self._stop_requested, self._emit_event, self._commands)
        except Exception as exc:
            self._emit_event(RuntimeEvent(RuntimeEventKind.ERROR, f"TDLib could not start: {exc}"))
            self._emit_event(RuntimeEvent(RuntimeEventKind.STOPPED, "TDLib did not start"))

    def _emit_event(self, event: RuntimeEvent) -> None:
        self.event_received.emit(event)
