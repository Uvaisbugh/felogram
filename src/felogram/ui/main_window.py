from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget

from felogram.telegram.runtime import RuntimeEvent, RuntimeEventKind, TdRuntime
from felogram.ui.runtime_thread import TdRuntimeThread


class MainWindow(QMainWindow):
    def __init__(
        self,
        runtime_factory: Callable[[], TdRuntime],
        *,
        auto_start: bool = True,
    ) -> None:
        super().__init__()
        self.setWindowTitle("Felogram")
        self.resize(520, 300)

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

        self._close_button = QPushButton("Close")
        self._close_button.clicked.connect(self.close)

        layout = QVBoxLayout()
        layout.setContentsMargins(36, 36, 36, 36)
        layout.setSpacing(14)
        layout.addWidget(self._title)
        layout.addWidget(self._status)
        layout.addWidget(self._version)
        layout.addWidget(self._heartbeat)
        layout.addStretch()
        layout.addWidget(self._close_button)

        content = QWidget()
        content.setLayout(layout)
        self.setCentralWidget(content)

        self.setStyleSheet(
            "#titleLabel { font-size: 28px; font-weight: 600; }"
            "#statusLabel { font-size: 16px; }"
            "#versionLabel, #heartbeatLabel { color: #666; }"
            "QPushButton { padding: 8px 18px; }"
        )

        self._timer = QTimer(self)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self._update_heartbeat)
        self._timer.start()

        self._runtime_thread = TdRuntimeThread(runtime_factory, self)
        self._runtime_thread.event_received.connect(self._on_runtime_event)
        self._runtime_thread.finished.connect(self._on_runtime_finished)
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
        if event.kind == RuntimeEventKind.VERSION:
            self._version.setText(event.message)
        else:
            self._status.setText(event.message)

    def _on_runtime_finished(self) -> None:
        if self._closing_requested:
            self._allow_close = True
            QTimer.singleShot(0, self.close)
