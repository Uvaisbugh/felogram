from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from felogram.telegram.runtime import RuntimeCommand, RuntimeEvent, RuntimeEventKind
from felogram.telegram.transport import JsonObject


class ChatWidget(QWidget):
    """Read-only main chat list and paginated history."""

    command_submitted = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._chats: dict[int, JsonObject] = {}
        self._orders: dict[int, int] = {}
        self._messages: dict[int, JsonObject] = {}
        self._chat_id: int | None = None
        self._generation = 0
        self._pending: str | None = None
        self._ready = False
        self._load_pending = False
        layout = QVBoxLayout(self)
        self.status = QLabel("Sign in to load chats. This preview is read-only.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.load = QPushButton("Load more chats")
        self.load.setEnabled(False)
        self.load.clicked.connect(self._load_chats)
        layout.addWidget(self.load)
        row = QHBoxLayout()
        self.chats = QListWidget()
        self.chats.setAccessibleName("Telegram chats")
        self.chats.currentItemChanged.connect(self._select_chat)
        row.addWidget(self.chats, 1)
        self.history = QTextEdit()
        self.history.setReadOnly(True)
        self.history.setAccessibleName("Message history")
        row.addWidget(self.history, 2)
        layout.addLayout(row)
        self.older = QPushButton("Load older messages")
        self.older.setEnabled(False)
        self.older.clicked.connect(self._load_history)
        layout.addWidget(self.older)

    def handle_event(self, event: RuntimeEvent) -> None:
        data = event.data or {}
        if event.kind == RuntimeEventKind.AUTHORIZATION:
            ready = event.message == "authorizationStateReady"
            if ready and not self._ready:
                self._ready = True
                self._load_chats()
            elif not ready:
                self._ready = False
                self._generation += 1
                self._pending = None
                self._load_pending = False
                self._chat_id = None
                self._chats.clear()
                self._orders.clear()
                self._messages.clear()
                self.chats.clear()
                self.history.clear()
                self.older.setEnabled(False)
            self.load.setEnabled(ready and not self._load_pending)
        elif event.kind == RuntimeEventKind.RESPONSE:
            if event.message == "Load chats":
                self._load_pending = False
                self.load.setEnabled(self._ready)
                self.status.setText(
                    "Unable to load more chats (or end of list)."
                    if data.get("@type") == "error"
                    else "Select a chat to read its history."
                )
            elif self._ready and event.message == self._pending:
                self._pending = None
                if data.get("@type") == "error":
                    self.status.setText("History request failed. You can try again.")
                    self.older.setEnabled(self._ready)
                    return
                messages = data.get("messages")
                if isinstance(messages, list):
                    previous_oldest = min(self._messages, default=0)
                    for message in messages:
                        self._add_message(message)
                    self._render_history()
                    oldest = min(self._messages, default=0)
                    progressed = oldest > 0 and (previous_oldest == 0 or oldest < previous_oldest)
                    self.older.setEnabled(progressed and self._ready)
                    self.status.setText(
                        "History loaded." if messages else "No older messages returned."
                    )
        elif event.kind == RuntimeEventKind.UPDATE and self._ready:
            self._handle_update(data)
        elif event.kind in {RuntimeEventKind.STOPPING, RuntimeEventKind.STOPPED}:
            self._ready = False
            self.load.setEnabled(False)
            self.older.setEnabled(False)

    def _load_chats(self) -> None:
        if not self._ready or self._load_pending:
            return
        self._load_pending = True
        self.load.setEnabled(False)
        self.command_submitted.emit(
            RuntimeCommand(
                "Load chats",
                {"@type": "loadChats", "chat_list": {"@type": "chatListMain"}, "limit": 50},
            )
        )

    def _handle_update(self, data: JsonObject) -> None:
        kind = data.get("@type")
        chat_id = data.get("chat_id")
        if kind == "updateNewChat":
            chat = data.get("chat")
            if isinstance(chat, dict) and isinstance(chat.get("id"), int):
                identifier = chat["id"]
                assert isinstance(identifier, int)
                self._chats[identifier] = chat
                self._set_positions(identifier, chat.get("positions"))
        elif isinstance(chat_id, int):
            if kind == "updateChatPosition":
                self._set_positions(chat_id, [data.get("position")])
            elif kind == "updateChatLastMessage":
                self._orders[chat_id] = 0
                self._set_positions(chat_id, data.get("positions"))
            elif kind == "updateChatTitle" and chat_id in self._chats:
                self._chats[chat_id]["title"] = data.get("title")
            elif kind == "updateDeleteMessages" and chat_id == self._chat_id:
                ids = data.get("message_ids")
                if isinstance(ids, list):
                    for identifier in ids:
                        if isinstance(identifier, int):
                            self._messages.pop(identifier, None)
                    self._render_history()
            elif kind == "updateMessageContent" and chat_id == self._chat_id:
                identifier = data.get("message_id")
                if isinstance(identifier, int) and identifier in self._messages:
                    self._messages[identifier]["content"] = data.get("new_content")
                    self._render_history()
        if kind == "updateNewMessage":
            self._add_message(data.get("message"))
            self._render_history()
        if kind in {
            "updateNewChat",
            "updateChatPosition",
            "updateChatLastMessage",
            "updateChatTitle",
        }:
            self._render_chats()
        elif kind == "updateConnectionState":
            state = data.get("state")
            if isinstance(state, dict):
                self.status.setText(f"Connection: {state.get('@type', 'unknown')}")

    def _set_positions(self, chat_id: int, positions: object) -> None:
        if not isinstance(positions, list):
            return
        for position in positions:
            if not isinstance(position, dict):
                continue
            chat_list = position.get("list")
            if isinstance(chat_list, dict) and chat_list.get("@type") == "chatListMain":
                order = position.get("order", 0)
                try:
                    self._orders[chat_id] = int(str(order))
                except ValueError:
                    continue

    def _render_chats(self) -> None:
        self.chats.blockSignals(True)
        self.chats.clear()
        for chat_id in sorted(self._chats, key=lambda x: (self._orders.get(x, 0), x), reverse=True):
            if self._orders.get(chat_id, 0) <= 0:
                continue
            item = QListWidgetItem(str(self._chats[chat_id].get("title", "Untitled chat")))
            item.setData(Qt.ItemDataRole.UserRole, chat_id)
            self.chats.addItem(item)
            if chat_id == self._chat_id:
                self.chats.setCurrentItem(item)
        self.chats.blockSignals(False)

    def _select_chat(
        self, current: QListWidgetItem | None, previous: QListWidgetItem | None
    ) -> None:
        del previous
        if current is None or not self._ready:
            return
        self._chat_id = int(current.data(Qt.ItemDataRole.UserRole))
        self._generation += 1
        self._pending = None
        self._messages.clear()
        self.history.clear()
        self._load_history()

    def _load_history(self) -> None:
        if self._chat_id is None or not self._ready or self._pending:
            return
        self._generation += 1
        self._pending = f"History:{self._chat_id}:{self._generation}"
        self.older.setEnabled(False)
        self.status.setText("Loading history…")
        self.command_submitted.emit(
            RuntimeCommand(
                self._pending,
                {
                    "@type": "getChatHistory",
                    "chat_id": self._chat_id,
                    "from_message_id": min(self._messages, default=0),
                    "offset": 0,
                    "limit": 50,
                    "only_local": False,
                },
            )
        )

    def _add_message(self, message: object) -> None:
        if (
            isinstance(message, dict)
            and message.get("chat_id") == self._chat_id
            and isinstance(message.get("id"), int)
        ):
            self._messages[message["id"]] = message

    def _render_history(self) -> None:
        lines: list[str] = []
        for identifier in sorted(self._messages):
            message = self._messages[identifier]
            content = message.get("content")
            text = "[Unsupported message]"
            if isinstance(content, dict):
                formatted = content.get("text") or content.get("caption")
                if isinstance(formatted, dict) and isinstance(formatted.get("text"), str):
                    text = str(formatted["text"])
                else:
                    text = f"[{content.get('@type', 'Unsupported message')}]"
            sender = message.get("sender_id")
            label = "Unknown sender"
            if isinstance(sender, dict):
                label = str(sender.get("user_id") or sender.get("chat_id") or label)
            lines.append(f"{label}:\n{text}")
        self.history.setPlainText("\n\n".join(lines))
