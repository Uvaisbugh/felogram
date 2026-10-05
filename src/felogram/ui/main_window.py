from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QLabel, QMainWindow, QPushButton, QTabWidget, QVBoxLayout, QWidget

from felogram.application.auth import AppPaths, AuthRequestFactory
from felogram.application.preferences import PreferenceStore
from felogram.telegram.runtime import RuntimeEvent, RuntimeEventKind, TdRuntime
from felogram.ui.auth_widget import AuthWidget
from felogram.ui.chat_widget import ChatWidget
from felogram.ui.runtime_thread import TdRuntimeThread
from felogram.ui.snippet_widget import SnippetWidget


class MainWindow(QMainWindow):
    def __init__(
        self,
        runtime_factory: Callable[[], TdRuntime],
        *,
        auto_start: bool = True,
        auth_factory: AuthRequestFactory | None = None,
    ) -> None:
        super().__init__()
        self.setWindowTitle("Felogram")
        self.resize(1180, 900)

        self._closing_requested = False
        self._allow_close = False
        self._ticks = 0

        self._title = QLabel("Felogram")
        self._title.setObjectName("titleLabel")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._status = QLabel("Application initialized")
        self._status.setObjectName("statusLabel")
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._version = QLabel("TDLib version: checking...")
        self._version.setObjectName("versionLabel")
        self._version.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._heartbeat = QLabel("UI heartbeat: 0")
        self._heartbeat.setObjectName("heartbeatLabel")
        self._heartbeat.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._auth = AuthWidget(auth_factory)
        tabs = QTabWidget()
        tabs.addTab(self._auth, "Telegram account")
        store = (
            PreferenceStore(AppPaths.default().data_root / "workspace.dpapi")
            if auto_start
            else None
        )
        self._chats = ChatWidget(store=store)
        tabs.addTab(self._chats, "Chats")
        tabs.addTab(SnippetWidget(), "Code snippets")
        tagline = QLabel("Telegram for developers · Early alpha")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._close_button = QPushButton("Close")
        self._close_button.clicked.connect(self.close)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        layout.addWidget(self._title)
        layout.addWidget(tagline)
        layout.addWidget(self._status)
        layout.addWidget(self._version)
        layout.addWidget(tabs, 1)
        layout.addWidget(self._heartbeat)
        layout.addWidget(self._close_button)

        content = QWidget()
        content.setLayout(layout)
        self.setCentralWidget(content)

        self.setStyleSheet(
            "#titleLabel { font-size: 28px; font-weight: 600; }"
            "#statusLabel { font-size: 16px; }"
            "#versionLabel, #heartbeatLabel { color: #666; }"
            "#authHeading { font-size: 20px; font-weight: 600; margin-bottom: 8px; }"
            "QLineEdit { padding: 8px; }"
            "QPushButton { padding: 8px 18px; }"
        )

        self._timer = QTimer(self)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self._update_heartbeat)
        self._timer.start()

        self._runtime_thread = TdRuntimeThread(runtime_factory, self)
        self._runtime_thread.event_received.connect(self._on_runtime_event)
        self._runtime_thread.finished.connect(self._on_runtime_finished)
        self._auth.command_submitted.connect(self._runtime_thread.submit)
        self._chats.command_submitted.connect(self._runtime_thread.submit)
        self._auth.input_error.connect(self._show_input_error)
        if auto_start:
            self._runtime_thread.start()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._allow_close or not self._runtime_thread.isRunning():
            event.accept()
            return

        event.ignore()
        if self._closing_requested:
            return
        self._closing_requested = True
        self._close_button.setEnabled(False)
        self._status.setText("Closing TDLib...")
        self._runtime_thread.request_stop()

    def _update_heartbeat(self) -> None:
        self._ticks += 1
        self._heartbeat.setText(f"UI heartbeat: {self._ticks}")

    def _on_runtime_event(self, event: object) -> None:
        if not isinstance(event, RuntimeEvent):
            return
        self._chats.handle_event(event)
        if event.kind == RuntimeEventKind.VERSION:
            self._version.setText(event.message)
        elif event.kind == RuntimeEventKind.AUTHORIZATION:
            state = event.data or {"@type": event.message}
            self._auth.handle_authorization(state)
            self._status.setText(self._auth.friendly_state(event.message))
        elif event.kind not in {RuntimeEventKind.RESPONSE, RuntimeEventKind.UPDATE}:
            self._status.setText(event.message)

    def _show_input_error(self, message: str) -> None:
        self._status.setText(message)

    def _on_runtime_finished(self) -> None:
        if self._closing_requested:
            self._allow_close = True
            QTimer.singleShot(0, self.close)
