from __future__ import annotations

from PySide6.QtWidgets import QLabel, QStackedWidget
from pytestqt.qtbot import QtBot

from felogram.telegram.runtime import RuntimeEvent, RuntimeEventKind, TdRuntime
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


def test_window_shows_page_for_authorization_state(qtbot: QtBot) -> None:
    window = MainWindow(unused_runtime, auto_start=False)
    qtbot.addWidget(window)

    window._on_runtime_event(
        RuntimeEvent(
            RuntimeEventKind.AUTHORIZATION,
            "authorizationStateWaitPhoneNumber",
            {"@type": "authorizationStateWaitPhoneNumber"},
        )
    )

    pages = window.findChild(QStackedWidget, "authPages")
    status = window.findChild(QLabel, "statusLabel")
    assert pages is not None
    assert pages.currentWidget() is not None
    assert pages.currentWidget().objectName() == "authPhonePage"
    assert status is not None
    assert status.text() == "Enter your Telegram phone number"
