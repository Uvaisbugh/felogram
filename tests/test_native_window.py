from __future__ import annotations

import pytest
from PySide6.QtWidgets import QLabel
from pytestqt.qtbot import QtBot

from felogram.main import create_runtime
from felogram.ui.main_window import MainWindow


@pytest.mark.native
def test_native_runtime_keeps_window_responsive_and_closes(qtbot: QtBot) -> None:
    window = MainWindow(create_runtime)
    qtbot.addWidget(window)
    window.show()

    version = window.findChild(QLabel, "versionLabel")
    heartbeat = window.findChild(QLabel, "heartbeatLabel")
    assert version is not None
    assert heartbeat is not None

    qtbot.waitUntil(lambda: version.text() == "TDLib 1.8.67", timeout=5_000)
    qtbot.waitUntil(lambda: heartbeat.text() != "UI heartbeat: 0", timeout=1_000)

    window.close()
    qtbot.waitUntil(lambda: not window.isVisible(), timeout=7_000)
