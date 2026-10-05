from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from felogram.application.auth import AppPaths, AuthRequestFactory
from felogram.logging_config import configure_logging
from felogram.telegram.runtime import RuntimeEvent, RuntimeEventKind, TdRuntime
from felogram.telegram.tdjson_adapter import TdjsonTransport
from felogram.ui.main_window import MainWindow


def create_runtime() -> TdRuntime:
    return TdRuntime(TdjsonTransport())


def main() -> int:
    configure_logging()
    if "--probe" in sys.argv:
        from felogram.probe import main as probe

        return probe()
    app = QApplication(sys.argv)
    app.setApplicationName("Felogram")
    smoke = "--smoke-test" in sys.argv
    auth = (
        AuthRequestFactory(AppPaths(Path(tempfile.gettempdir()) / f"felogram-smoke-{uuid4()}"))
        if smoke
        else None
    )
    window = MainWindow(create_runtime, auth_factory=auth)
    window.show()
    events: list[RuntimeEvent] = []
    if smoke:

        def capture(event: object) -> None:
            if isinstance(event, RuntimeEvent):
                events.append(event)

        window._runtime_thread.event_received.connect(capture)
        QTimer.singleShot(1500, window.close)
    result = app.exec()
    if smoke:
        succeeded = any(event.kind == RuntimeEventKind.VERSION for event in events)
        closed = any(event.message == "TDLib closed cleanly" for event in events)
        errors = any(event.kind == RuntimeEventKind.ERROR for event in events)
        print(
            "Desktop smoke test passed"
            if succeeded and closed and not errors
            else "Desktop smoke test failed"
        )
        return 0 if succeeded and closed and not errors else 1
    return result
