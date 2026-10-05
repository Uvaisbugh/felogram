from __future__ import annotations

import time
from html import escape

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from felogram.application.messaging import (
    Outbox,
    code_blocks,
    formatted_content,
    render_content,
    send_text,
)
from felogram.application.preferences import Preferences, PreferenceStore
from felogram.security import SecretStoreError
from felogram.telegram.runtime import RuntimeCommand, RuntimeEvent, RuntimeEventKind
from felogram.telegram.transport import JsonObject


class ChatWidget(QWidget):
    """Chats, explicit sends, local organization, and paginated search."""

    command_submitted = Signal(object)

    def __init__(
        self, parent: QWidget | None = None, *, store: PreferenceStore | None = None
    ) -> None:
        super().__init__(parent)
        self._chats: dict[int, JsonObject] = {}
        self._orders: dict[int, int] = {}
        self._messages: dict[int, JsonObject] = {}
        self._chat_id: int | None = None
        self._generation = 0
        self._pending: str | None = None
        self._ready = False
        self._load_pending = False
        self._query = ""
        self._search_from = 0
        self._outbox = Outbox()
        self._send_operation: str | None = None
        self._submitted_text = ""
        self._drafts: dict[int, tuple[str, str, bool]] = {}
        self._delivery_updates: dict[int, JsonObject] = {}
        self._text_limit = 4096
        self._users: dict[int, str] = {}
        self._self_id: int | None = None
        self._preferences_owner: int | None = None
        self._store = store or PreferenceStore()
        self._base_store = self._store
        preference_error = ""
        try:
            self._preferences = self._store.load()
        except OSError, ValueError, SecretStoreError:
            self._preferences = Preferences()
            preference_error = "Local preferences could not be loaded."
        layout = QVBoxLayout(self)
        self.status = QLabel(preference_error or "Sign in to load chats.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.load = QPushButton("Load more chats")
        self.load.setEnabled(False)
        self.load.clicked.connect(self._load_chats)
        layout.addWidget(self.load)
        filters = QHBoxLayout()
        self.chat_filter = QLineEdit()
        self.chat_filter.setPlaceholderText("Filter chats (Ctrl+K)")
        self.chat_filter.setAccessibleName("Filter chats by title")
        self.chat_filter.textChanged.connect(self._render_chats)
        filters.addWidget(self.chat_filter)
        self.unread = QCheckBox("Unread only")
        self.unread.toggled.connect(self._render_chats)
        filters.addWidget(self.unread)
        self.collection = QComboBox()
        self.collection.setEditable(True)
        self.collection.setAccessibleName("Local chat collection")
        self.collection.addItems(["All chats", *self._preferences.collections])
        self.collection.currentTextChanged.connect(self._render_chats)
        filters.addWidget(self.collection)
        self.collect = QPushButton("Add chat")
        self.collect.setToolTip("Type a collection name, then add the selected chat locally.")
        self.collect.clicked.connect(self._collect_chat)
        filters.addWidget(self.collect)
        self.remove_collection_chat = QPushButton("Remove chat")
        self.remove_collection_chat.clicked.connect(self._remove_collection_chat)
        filters.addWidget(self.remove_collection_chat)
        layout.addLayout(filters)
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
        search_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search messages in this chat (Ctrl+F)")
        self.search.setAccessibleName("Search messages")
        self.search.returnPressed.connect(self._search_messages)
        search_row.addWidget(self.search)
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self._search_messages)
        search_row.addWidget(self.search_button)
        self.save_search = QPushButton("Save search")
        self.save_search.clicked.connect(self._save_search)
        search_row.addWidget(self.save_search)
        self.back = QPushButton("Back to history")
        self.back.clicked.connect(self._back_to_history)
        search_row.addWidget(self.back)
        layout.addLayout(search_row)
        self.saved_searches = QComboBox()
        self.saved_searches.setAccessibleName("Saved message searches")
        self._populate_searches()
        self.saved_searches.activated.connect(self._use_saved_search)
        layout.addWidget(self.saved_searches)
        self.older = QPushButton("Load older messages")
        self.older.setEnabled(False)
        self.older.clicked.connect(self._load_history)
        layout.addWidget(self.older)
        code_row = QHBoxLayout()
        self.codes = QComboBox()
        self.codes.setAccessibleName("Code blocks in visible messages")
        code_row.addWidget(self.codes)
        self.copy_code = QPushButton("Copy code")
        self.copy_code.clicked.connect(self._copy_code)
        code_row.addWidget(self.copy_code)
        layout.addLayout(code_row)
        self.composer = QPlainTextEdit()
        self.composer.setPlaceholderText("Write a message (Ctrl+Enter to send)")
        self.composer.setAccessibleName("Message draft")
        self.composer.setMaximumHeight(100)
        layout.addWidget(self.composer)
        send_row = QHBoxLayout()
        self.as_code = QCheckBox("Send as code")
        send_row.addWidget(self.as_code)
        self.language = QLineEdit()
        self.language.setPlaceholderText("Code language")
        self.language.setAccessibleName("Code message language")
        send_row.addWidget(self.language)
        self.send = QPushButton("Send")
        self.send.clicked.connect(self._send_message)
        send_row.addWidget(self.send)
        self.retry = QPushButton("Retry failed send")
        self.retry.clicked.connect(self._retry_send)
        send_row.addWidget(self.retry)
        self.check_delivery = QPushButton("Check delivery")
        self.check_delivery.clicked.connect(self._check_delivery)
        send_row.addWidget(self.check_delivery)
        self.dismiss = QPushButton("Dismiss failed send")
        self.dismiss.clicked.connect(self._dismiss_failed)
        send_row.addWidget(self.dismiss)
        layout.addLayout(send_row)
        self.delivery = QLabel("Messages are sent only when you press Send.")
        self.delivery.setWordWrap(True)
        layout.addWidget(self.delivery)
        help_button = QPushButton("Keyboard shortcuts (F1)")
        help_button.clicked.connect(self._show_shortcuts)
        layout.addWidget(help_button)
        for key, action in (
            ("Ctrl+K", self.chat_filter.setFocus),
            ("Ctrl+F", self.search.setFocus),
            ("Ctrl+L", self.composer.setFocus),
            ("Ctrl+Return", self._send_message),
            ("Alt+Left", self._back_to_history),
            ("F1", self._show_shortcuts),
        ):
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(action)
        self._retry_timer = QTimer(self)
        self._retry_timer.setInterval(1000)
        self._retry_timer.timeout.connect(self._update_send_controls)
        self._retry_timer.start()
        self._update_send_controls()

    def handle_event(self, event: RuntimeEvent) -> None:
        data = event.data or {}
        if event.kind == RuntimeEventKind.AUTHORIZATION:
            ready = event.message == "authorizationStateReady"
            if ready and not self._ready:
                self._ready = True
                self._load_chats()
                self.command_submitted.emit(
                    RuntimeCommand(
                        "Message length limit",
                        {"@type": "getOption", "name": "message_text_length_max"},
                    )
                )
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
                self._drafts.clear()
                self.composer.clear()
                self._delivery_updates.clear()
                self._outbox.attempt = None
                self._send_operation = None
                self._users.clear()
                self.codes.clear()
                self._preferences = Preferences()
                self._preferences_owner = None
                self._self_id = None
                self._store = self._base_store
                self._populate_searches()
                self.collection.clear()
                self.collection.addItem("All chats")
            self._update_send_controls()
            self.load.setEnabled(ready and not self._load_pending)
        elif event.kind == RuntimeEventKind.RESPONSE:
            if self._handle_send_response(event):
                return
            if event.message == "Message length limit":
                value = data.get("value")
                try:
                    if isinstance(value, (str, int)) and int(value) > 0:
                        self._text_limit = int(value)
                except ValueError:
                    pass
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
                    if self._query:
                        next_id = data.get("next_from_message_id")
                        self._search_from = next_id if isinstance(next_id, int) else 0
                        self.older.setEnabled(self._search_from > 0 and self._ready)
        elif event.kind == RuntimeEventKind.UPDATE:
            if self._ready or data.get("@type") == "updateOption":
                self._handle_update(data)
        elif event.kind in {RuntimeEventKind.STOPPING, RuntimeEventKind.STOPPED}:
            self._ready = False
            self.load.setEnabled(False)
            self.older.setEnabled(False)
            self._update_send_controls()

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
        if kind == "updateOption" and data.get("name") == "my_id":
            value = data.get("value")
            if isinstance(value, dict):
                identifier = value.get("value")
                if isinstance(identifier, (str, int)):
                    try:
                        self._self_id = int(identifier)
                        self._load_account_preferences()
                    except ValueError:
                        pass
        if kind in {"updateMessageSendSucceeded", "updateMessageSendFailed"}:
            message = data.get("message")
            old_id = data.get("old_message_id")
            if isinstance(message, dict) and isinstance(old_id, int):
                if (
                    self._outbox.attempt is not None
                    and message.get("chat_id") == self._outbox.attempt.chat_id
                ):
                    self._delivery_updates[old_id] = message
                attempt = self._outbox.attempt
                if (
                    attempt
                    and attempt.message_id == old_id
                    and message.get("chat_id") == attempt.chat_id
                ):
                    self._outbox.accept(message)
                    self._show_delivery()
                if message.get("chat_id") == self._chat_id:
                    self._messages.pop(old_id, None)
                    if not self._query:
                        self._add_message(message)
                    self._render_history()
            return
        if kind == "updateUser":
            user = data.get("user")
            if isinstance(user, dict) and isinstance(user.get("id"), int):
                identifier = user["id"]
                assert isinstance(identifier, int)
                self._users[identifier] = (
                    f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
                )
                self._render_history()
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
            elif kind == "updateChatReadInbox" and chat_id in self._chats:
                self._chats[chat_id]["unread_count"] = data.get("unread_count", 0)
                self._render_chats()
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
            message = data.get("message")
            if not self._query or (
                isinstance(message, dict) and message.get("id") in self._messages
            ):
                self._add_message(message)
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
            chat = self._chats[chat_id]
            title = str(chat.get("title", "Untitled chat"))
            if self.chat_filter.text().casefold() not in title.casefold():
                continue
            unread = chat.get("unread_count", 0)
            if self.unread.isChecked() and (not isinstance(unread, int) or unread <= 0):
                continue
            collection = self.collection.currentText()
            if collection != "All chats" and chat_id not in self._preferences.collections.get(
                collection, []
            ):
                continue
            item = QListWidgetItem(title + (f" ({unread})" if unread else ""))
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
        if self._chat_id is not None:
            self._drafts[self._chat_id] = (
                self.composer.toPlainText(),
                self.language.text(),
                self.as_code.isChecked(),
            )
        self._chat_id = int(current.data(Qt.ItemDataRole.UserRole))
        draft, language, code = self._drafts.get(self._chat_id, ("", "", False))
        self.composer.setPlainText(draft)
        self.language.setText(language)
        self.as_code.setChecked(code)
        self._query = ""
        self.search.clear()
        self._update_send_controls()
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
        request: JsonObject = {
            "@type": "getChatHistory",
            "chat_id": self._chat_id,
            "from_message_id": min(self._messages, default=0),
            "offset": 0,
            "limit": 50,
            "only_local": False,
        }
        if self._query:
            request.update(
                {
                    "@type": "searchChatMessages",
                    "query": self._query,
                    "topic_id": None,
                    "sender_id": None,
                    "filter": None,
                    "from_message_id": self._search_from,
                }
            )
        self.command_submitted.emit(RuntimeCommand(self._pending, request))

    def _add_message(self, message: object) -> None:
        if (
            isinstance(message, dict)
            and message.get("chat_id") == self._chat_id
            and isinstance(message.get("id"), int)
        ):
            self._messages[message["id"]] = message

    def _render_history(self) -> None:
        lines: list[str] = []
        self.codes.clear()
        for identifier in sorted(self._messages):
            message = self._messages[identifier]
            formatted = formatted_content(message)
            for _, _, block in code_blocks(formatted):
                self.codes.addItem(f"{identifier}: {block.language or 'code'}", block.text)
            sender = message.get("sender_id")
            label = "Unknown sender"
            if isinstance(sender, dict):
                label = str(sender.get("user_id") or sender.get("chat_id") or label)
                user_id = sender.get("user_id")
                if isinstance(user_id, int):
                    label = self._users.get(user_id, label)
            sending = message.get("sending_state")
            state = ""
            if isinstance(sending, dict):
                state = (
                    " · failed"
                    if sending.get("@type") == "messageSendingStateFailed"
                    else " · pending"
                )
            lines.append(f"<p><b>{escape(label)}{state}</b></p>{render_content(formatted)}<hr>")
        scroll = self.history.verticalScrollBar().value()
        self.history.setHtml("".join(lines))
        self.history.verticalScrollBar().setValue(scroll)
        self.copy_code.setEnabled(self.codes.count() > 0)

    def _update_send_controls(self) -> None:
        attempt = self._outbox.attempt
        self.send.setEnabled(self._ready and self._chat_id is not None and attempt is None)
        self.retry.setEnabled(
            self._ready
            and attempt is not None
            and attempt.state == "failed"
            and attempt.can_retry
            and time.monotonic() >= attempt.retry_at
        )
        self.dismiss.setEnabled(self._ready and attempt is not None and attempt.state == "failed")
        self.check_delivery.setEnabled(
            self._ready
            and attempt is not None
            and attempt.message_id is not None
            and attempt.state != "requesting"
        )

    def _send_message(self) -> None:
        if not self._ready or self._chat_id is None:
            self.delivery.setText("Sign in and select a chat first.")
            return
        try:
            text = self.composer.toPlainText()
            request = send_text(
                self._chat_id,
                text,
                limit=self._text_limit,
                language=self.language.text() if self.as_code.isChecked() else None,
            )
            command = self._outbox.start(self._chat_id, request)
        except ValueError as exc:
            self.delivery.setText(str(exc))
            return
        self._submitted_text = text
        self._send_operation = command.operation
        self._delivery_updates.clear()
        self.delivery.setText("Submitting message…")
        self._update_send_controls()
        self.command_submitted.emit(command)

    def _handle_send_response(self, event: RuntimeEvent) -> bool:
        attempt = self._outbox.attempt
        if attempt is None or event.message != self._send_operation:
            return False
        data = event.data or {}
        self._send_operation = None
        if data.get("@type") == "error":
            if attempt.message_id is None:
                self._outbox.attempt = None
                self.delivery.setText("Telegram rejected this send. Your draft is preserved.")
            else:
                attempt.state = "uncertain"
                self.delivery.setText(
                    "Delivery check or retry failed. Check delivery before trying again."
                )
            self._update_send_controls()
            return True
        message: JsonObject | None = None
        if data.get("@type") == "message":
            message = data
        elif data.get("@type") == "messages":
            messages = data.get("messages")
            if isinstance(messages, list) and messages and isinstance(messages[0], dict):
                message = messages[0]
        if (
            message is None
            or message.get("chat_id") != attempt.chat_id
            or not isinstance(message.get("id"), int)
        ):
            attempt.state = "uncertain"
            self.delivery.setText("Delivery is unknown. No automatic resend will occur.")
            self._update_send_controls()
            return True
        chat_id = attempt.chat_id
        self._outbox.accept(message)
        identifier = message.get("id")
        final = (
            self._delivery_updates.pop(identifier, None) if isinstance(identifier, int) else None
        )
        if final is not None:
            self._outbox.accept(final)
            message = final
        if chat_id == self._chat_id and self.composer.toPlainText() == self._submitted_text:
            self.composer.clear()
        elif chat_id in self._drafts and self._drafts[chat_id][0] == self._submitted_text:
            self._drafts.pop(chat_id)
        if not self._query:
            self._add_message(message)
            self._render_history()
        self._show_delivery()
        return True

    def _show_delivery(self) -> None:
        attempt = self._outbox.attempt
        if attempt is None:
            self.delivery.setText("Message sent.")
            self._delivery_updates.clear()
        elif attempt.state == "failed":
            self.delivery.setText(
                "Message failed. Retry is available only when Telegram permits it."
            )
        else:
            self.delivery.setText("Message pending. Waiting for Telegram's delivery result.")
        self._update_send_controls()

    def _retry_send(self) -> None:
        if not self._ready:
            return
        try:
            command = self._outbox.retry()
        except ValueError as exc:
            self.delivery.setText(str(exc))
            return
        self._send_operation = command.operation
        self.delivery.setText("Retrying the existing failed message…")
        self._update_send_controls()
        self.command_submitted.emit(command)

    def _check_delivery(self) -> None:
        attempt = self._outbox.attempt
        if not self._ready or attempt is None or attempt.message_id is None:
            return
        attempt.operation = f"Delivery:{attempt.chat_id}:{attempt.message_id}:{time.monotonic()}"
        attempt.state = "requesting"
        self._send_operation = attempt.operation
        self._update_send_controls()
        self.command_submitted.emit(
            RuntimeCommand(
                attempt.operation,
                {
                    "@type": "getMessage",
                    "chat_id": attempt.chat_id,
                    "message_id": attempt.message_id,
                },
            )
        )

    def _dismiss_failed(self) -> None:
        attempt = self._outbox.attempt
        if attempt is not None and attempt.state == "failed":
            self._outbox.attempt = None
            self.delivery.setText("Failed send dismissed. The failed message remains in history.")
            self._update_send_controls()

    def _search_messages(self) -> None:
        if not self._ready or self._chat_id is None:
            return
        query = self.search.text().strip()
        if not query:
            self._back_to_history()
            return
        chat_type = self._chats.get(self._chat_id, {}).get("type")
        if isinstance(chat_type, dict) and chat_type.get("@type") == "chatTypeSecret":
            self.status.setText("Message search in secret chats is not available yet.")
            return
        self._query = query[:256]
        self._search_from = 0
        self._pending = None
        self._messages.clear()
        self.history.clear()
        self._load_history()

    def _back_to_history(self) -> None:
        if not self._ready or self._chat_id is None:
            return
        self._query = ""
        self.search.clear()
        self._pending = None
        self._messages.clear()
        self._load_history()

    def _save_preferences(self) -> None:
        try:
            self._store.save(self._preferences)
        except OSError, ValueError, SecretStoreError:
            self.status.setText("Unable to save local preferences. Changes remain in memory.")

    def _load_account_preferences(self) -> None:
        identifier = self._self_id
        path = self._base_store.path
        if (
            identifier is None
            or identifier <= 0
            or path is None
            or self._preferences_owner == identifier
        ):
            return
        self._store = PreferenceStore(path.with_name(f"workspace-{identifier}.dpapi"))
        try:
            self._preferences = self._store.load()
        except OSError, ValueError, SecretStoreError:
            self.status.setText("Account preferences could not be loaded; using memory only.")
            self._store = PreferenceStore()
            self._preferences = Preferences()
        self._preferences_owner = identifier
        self._populate_searches()
        self.collection.clear()
        self.collection.addItems(["All chats", *self._preferences.collections])
        self._render_chats()

    def _save_search(self) -> None:
        if self._chat_id is None or not self.search.text().strip():
            return
        item = (self._chat_id, self.search.text().strip()[:256])
        if item not in self._preferences.searches:
            self._preferences.searches.insert(0, item)
            self._preferences.searches = self._preferences.searches[:50]
            self._save_preferences()
            self._populate_searches()

    def _populate_searches(self) -> None:
        self.saved_searches.clear()
        self.saved_searches.addItem("Saved searches")
        for chat_id, query in self._preferences.searches:
            self.saved_searches.addItem(f"{chat_id}: {query}", (chat_id, query))

    def _use_saved_search(self, index: int) -> None:
        data = self.saved_searches.itemData(index)
        if not self._ready or not isinstance(data, (tuple, list)) or len(data) != 2:
            return
        chat_id, query = data
        self.collection.setCurrentText("All chats")
        self.chat_filter.clear()
        self.unread.setChecked(False)
        for row in range(self.chats.count()):
            item = self.chats.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == chat_id:
                self.chats.setCurrentItem(item)
                self.search.setText(str(query))
                self._search_messages()
                return
        self.status.setText("Load this search's chat before opening the saved search.")

    def _collect_chat(self) -> None:
        name = self.collection.currentText().strip()[:64]
        if self._chat_id is None or not name or name == "All chats":
            self.status.setText("Select a chat and type a new collection name first.")
            return
        ids = self._preferences.collections.setdefault(name, [])
        if self._chat_id not in ids:
            ids.append(self._chat_id)
        if self.collection.findText(name) < 0:
            self.collection.addItem(name)
        self._save_preferences()
        self._render_chats()

    def _remove_collection_chat(self) -> None:
        ids = self._preferences.collections.get(self.collection.currentText(), [])
        if self._chat_id in ids:
            ids.remove(self._chat_id)
            self._save_preferences()
            self._render_chats()

    def _copy_code(self) -> None:
        if self._chats.get(self._chat_id or 0, {}).get("has_protected_content") is True:
            self.status.setText("Copying is disabled for this protected chat.")
            return
        code = self.codes.currentData()
        if isinstance(code, str):
            QApplication.clipboard().setText(code)
            self.status.setText("Code copied.")

    def _show_shortcuts(self) -> None:
        QMessageBox.information(
            self,
            "Keyboard shortcuts",
            "Ctrl+K: filter chats\nCtrl+F: message search\nCtrl+L: message draft\n"
            "Ctrl+Enter: send\nAlt+Left: return to history\n"
            "Arrow keys: select chats\nTab / Shift+Tab: move between controls\nF1: this help",
        )
