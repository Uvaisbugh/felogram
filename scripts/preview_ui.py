"""Render the chat UI with synthetic data; never starts a Telegram client."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QTabWidget

from felogram.application.messaging import send_text
from felogram.telegram.runtime import RuntimeEvent, RuntimeEventKind, TdRuntime
from felogram.ui.main_window import MainWindow


def unused_runtime() -> TdRuntime:
    raise AssertionError("Preview must not connect to Telegram")


def main() -> None:
    app = QApplication([])
    window = MainWindow(unused_runtime, auto_start=False)
    window._on_runtime_event(
        RuntimeEvent(RuntimeEventKind.AUTHORIZATION, "authorizationStateReady")
    )
    for identifier, title in ((1, "Felogram development"), (2, "Python community")):
        window._on_runtime_event(
            RuntimeEvent(
                RuntimeEventKind.UPDATE,
                "updateNewChat",
                {
                    "@type": "updateNewChat",
                    "chat": {
                        "id": identifier,
                        "title": title,
                        "unread_count": 2 if identifier == 2 else 0,
                        "positions": [
                            {"list": {"@type": "chatListMain"}, "order": str(100 - identifier)}
                        ],
                    },
                },
            )
        )
    window._chats.chats.setCurrentRow(0)
    request = send_text(1, "def hello(name):\n    return f'Hello, {name}'", language="python")
    content = request["input_message_content"]
    assert isinstance(content, dict)
    window._chats._messages[1] = {
        "id": 1,
        "chat_id": 1,
        "sender_id": {"user_id": 42},
        "content": {"@type": "messageText", "text": content["text"]},
    }
    window._chats._users[42] = "Sample developer"
    window._chats._render_history()
    window.findChild(QTabWidget).setCurrentIndex(1)
    window._status.setText("Preview with synthetic data — no Telegram connection")
    window.show()
    app.processEvents()
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "build/chat-preview.png")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not window.grab().save(str(path)):
        raise RuntimeError("Unable to save preview")
    window.close()


if __name__ == "__main__":
    main()
