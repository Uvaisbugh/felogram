from __future__ import annotations

from PySide6.QtWidgets import QLabel
from pytestqt.qtbot import QtBot

from felogram.telegram.runtime import TdRuntime
from felogram.ui.main_window import MainWindow


def unused_runtime() -> TdRuntime:
    raise AssertionError("runtime should not start in this test")


def test_window_has_product_name_and_initial_status(qtbot: QtBot) -> None:
    window = MainWindow(unused_runtime, auto_start=False)
    qtbot.addWidget(window)
    window.show()

    status = window.findChild(QLabel, "statusLabel")
    assert window.windowTitle() == "Felogram"
    assert status is not None
    assert status.text() == "Application initialized"
