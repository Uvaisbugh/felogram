from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from felogram.logging_config import configure_logging
from felogram.telegram.runtime import TdRuntime
from felogram.telegram.tdjson_adapter import TdjsonTransport
from felogram.ui.main_window import MainWindow


def create_runtime() -> TdRuntime:
    return TdRuntime(TdjsonTransport())


def main() -> int:
    configure_logging()
    app = QApplication(sys.argv)
    app.setApplicationName("Felogram")
    window = MainWindow(create_runtime)
    window.show()
    return app.exec()
