from __future__ import annotations

from pytestqt.qtbot import QtBot

from felogram.telegram.runtime import RuntimeCommand, RuntimeEvent, RuntimeEventKind, TdRuntime
from felogram.ui.chat_widget import ChatWidget


def ready(widget: ChatWidget) -> None:
    widget.handle_event(RuntimeEvent(RuntimeEventKind.AUTHORIZATION, "authorizationStateReady"))


def add_chat(widget: ChatWidget, chat_id: int, order: str) -> None:
    widget.handle_event(
        RuntimeEvent(
            RuntimeEventKind.UPDATE,
            "updateNewChat",
            {
                "@type": "updateNewChat",
                "chat": {
                    "id": chat_id,
                    "title": f"Chat {chat_id}",
                    "positions": [{"list": {"@type": "chatListMain"}, "order": order}],
                },
            },
        )
    )


def test_chat_order_and_stale_history(qtbot: QtBot) -> None:
    widget = ChatWidget()
    qtbot.addWidget(widget)
    commands: list[RuntimeCommand] = []
    widget.command_submitted.connect(commands.append)
    ready(widget)
    assert commands[0].request["@type"] == "loadChats"
    add_chat(widget, 1, "100")
    add_chat(widget, 2, "200")
    assert widget.chats.item(0).text() == "Chat 2"
    widget.chats.setCurrentRow(1)
    old_request = commands[-1]
    widget.chats.setCurrentRow(0)
    widget.handle_event(
        RuntimeEvent(
            RuntimeEventKind.RESPONSE,
            old_request.operation,
            {"@type": "messages", "messages": [{"id": 1, "chat_id": 1}]},
        )
    )
    assert widget.history.toPlainText() == ""
    request = commands[-1]
    widget.handle_event(
        RuntimeEvent(
            RuntimeEventKind.RESPONSE,
            request.operation,
            {
                "@type": "messages",
                "messages": [
                    {
                        "id": 20,
                        "chat_id": 2,
                        "content": {"@type": "messageText", "text": {"text": "<b>code</b>"}},
                    }
                ],
            },
        )
    )
    assert "<b>code</b>" in widget.history.toPlainText()
    widget.older.click()
    assert commands[-1].request["from_message_id"] == 20


def test_history_errors_can_retry_and_logout_clears_private_data(qtbot: QtBot) -> None:
    widget = ChatWidget()
    qtbot.addWidget(widget)
    commands: list[RuntimeCommand] = []
    widget.command_submitted.connect(commands.append)
    ready(widget)
    add_chat(widget, 1, "100")
    widget.chats.setCurrentRow(0)
    widget.handle_event(
        RuntimeEvent(RuntimeEventKind.RESPONSE, commands[-1].operation, {"@type": "error"})
    )
    assert widget.older.isEnabled()
    widget.older.click()
    assert commands[-1].request["from_message_id"] == 0
    widget.handle_event(RuntimeEvent(RuntimeEventKind.AUTHORIZATION, "authorizationStateClosed"))
    assert widget.chats.count() == 0
    assert widget.history.toPlainText() == ""
    assert not widget.older.isEnabled()


def test_runtime_keeps_correlated_response_and_update_data() -> None:
    events: list[RuntimeEvent] = []
    pending = {"request-1": "History:1:1"}
    response = {"@type": "messages", "@extra": "request-1", "messages": []}
    TdRuntime._handle_response(response, "version", pending, events.append)
    assert events[0] == RuntimeEvent(RuntimeEventKind.RESPONSE, "History:1:1", response)
    assert pending == {}
    update = {"@type": "updateNewChat", "chat": {"id": 1}}
    TdRuntime._handle_response(update, "version", pending, events.append)
    assert events[-1] == RuntimeEvent(RuntimeEventKind.UPDATE, "updateNewChat", update)
