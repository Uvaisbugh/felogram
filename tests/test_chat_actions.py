from __future__ import annotations

from PySide6.QtWidgets import QApplication
from pytestqt.qtbot import QtBot

from felogram.telegram.runtime import RuntimeCommand, RuntimeEvent, RuntimeEventKind
from felogram.telegram.transport import JsonObject
from felogram.ui.chat_widget import ChatWidget


def setup_chat(qtbot: QtBot) -> tuple[ChatWidget, list[RuntimeCommand]]:
    widget = ChatWidget()
    qtbot.addWidget(widget)
    commands: list[RuntimeCommand] = []
    widget.command_submitted.connect(commands.append)
    widget.handle_event(RuntimeEvent(RuntimeEventKind.AUTHORIZATION, "authorizationStateReady"))
    for identifier in (1, 2):
        widget.handle_event(
            RuntimeEvent(
                RuntimeEventKind.UPDATE,
                "updateNewChat",
                {
                    "@type": "updateNewChat",
                    "chat": {
                        "id": identifier,
                        "title": f"Chat {identifier}",
                        "unread_count": identifier - 1,
                        "positions": [
                            {"list": {"@type": "chatListMain"}, "order": str(100 - identifier)}
                        ],
                    },
                },
            )
        )
    widget.chats.setCurrentRow(0)
    return widget, commands


def response(widget: ChatWidget, command: RuntimeCommand, data: JsonObject) -> None:
    widget.handle_event(RuntimeEvent(RuntimeEventKind.RESPONSE, command.operation, data))


def test_send_double_click_draft_and_pending_delivery(qtbot: QtBot) -> None:
    widget, commands = setup_chat(qtbot)
    widget.composer.setPlainText("hello")
    widget.send.click()
    command = commands[-1]
    widget._send_message()
    assert commands[-1] is command
    response(
        widget,
        command,
        {
            "@type": "message",
            "id": 10,
            "chat_id": 1,
            "sending_state": {"@type": "messageSendingStatePending"},
        },
    )
    assert widget.composer.toPlainText() == ""
    assert not widget.send.isEnabled()
    widget.handle_event(
        RuntimeEvent(
            RuntimeEventKind.UPDATE,
            "updateMessageSendSucceeded",
            {
                "@type": "updateMessageSendSucceeded",
                "old_message_id": 10,
                "message": {"@type": "message", "id": 20, "chat_id": 1, "sending_state": None},
            },
        )
    )
    assert widget.send.isEnabled()
    assert "sent" in widget.delivery.text()


def test_send_error_keeps_draft_and_early_success_is_correlated(qtbot: QtBot) -> None:
    widget, commands = setup_chat(qtbot)
    widget.composer.setPlainText("hello")
    widget.send.click()
    response(widget, commands[-1], {"@type": "error", "code": 400})
    assert widget.composer.toPlainText() == "hello"
    assert widget.send.isEnabled()
    widget.send.click()
    command = commands[-1]
    widget.handle_event(
        RuntimeEvent(
            RuntimeEventKind.UPDATE,
            "updateMessageSendSucceeded",
            {
                "@type": "updateMessageSendSucceeded",
                "old_message_id": 10,
                "message": {"@type": "message", "id": 20, "chat_id": 1, "sending_state": None},
            },
        )
    )
    response(
        widget,
        command,
        {
            "@type": "message",
            "id": 10,
            "chat_id": 1,
            "sending_state": {"@type": "messageSendingStatePending"},
        },
    )
    assert widget.send.isEnabled()


def test_search_pagination_and_back_ignore_stale_reply(qtbot: QtBot) -> None:
    widget, commands = setup_chat(qtbot)
    widget.search.setText("code")
    widget.search_button.click()
    command = commands[-1]
    assert command.request["@type"] == "searchChatMessages"
    response(
        widget,
        command,
        {
            "@type": "foundChatMessages",
            "messages": [{"id": 20, "chat_id": 1}],
            "next_from_message_id": 12,
        },
    )
    widget.older.click()
    old = commands[-1]
    assert old.request["from_message_id"] == 12
    widget.back.click()
    assert commands[-1].request["@type"] == "getChatHistory"
    response(widget, old, {"@type": "foundChatMessages", "messages": [{"id": 12, "chat_id": 1}]})
    assert 12 not in widget._messages


def test_local_filters_collections_and_saved_search_do_not_write_to_telegram(qtbot: QtBot) -> None:
    widget, commands = setup_chat(qtbot)
    before = len(commands)
    widget.collection.setEditText("Projects")
    widget.collect.click()
    assert widget.chats.count() == 1
    assert widget._preferences.collections == {"Projects": [1]}
    widget.collection.setCurrentText("All chats")
    widget.unread.setChecked(True)
    assert widget.chats.count() == 1
    assert widget.chats.item(0).text() == "Chat 2 (1)"
    widget.search.setText("build")
    widget.save_search.click()
    assert widget._preferences.searches == [(1, "build")]
    assert len(commands) == before


def test_code_display_and_copy_preserve_code(qtbot: QtBot) -> None:
    widget, commands = setup_chat(qtbot)
    response(
        widget,
        commands[-1],
        {
            "@type": "messages",
            "messages": [
                {
                    "id": 1,
                    "chat_id": 1,
                    "content": {
                        "@type": "messageText",
                        "text": {
                            "text": "print('<x>')",
                            "entities": [
                                {
                                    "offset": 0,
                                    "length": 12,
                                    "type": {
                                        "@type": "textEntityTypePreCode",
                                        "language": "python",
                                    },
                                }
                            ],
                        },
                    },
                }
            ],
        },
    )
    assert "python" in widget.history.toPlainText()
    widget.copy_code.click()
    assert QApplication.clipboard().text() == "print('<x>')"


def test_switching_chats_preserves_unsent_drafts(qtbot: QtBot) -> None:
    widget, _ = setup_chat(qtbot)
    widget.composer.setPlainText("draft 1")
    widget.chats.setCurrentRow(1)
    assert widget.composer.toPlainText() == ""
    widget.composer.setPlainText("draft 2")
    widget.chats.setCurrentRow(0)
    assert widget.composer.toPlainText() == "draft 1"


def test_failed_send_retry_and_connection_updates_do_not_duplicate_send(qtbot: QtBot) -> None:
    widget, commands = setup_chat(qtbot)
    widget.composer.setPlainText("hello")
    widget.send.click()
    response(
        widget,
        commands[-1],
        {
            "@type": "message",
            "id": 10,
            "chat_id": 1,
            "sending_state": {
                "@type": "messageSendingStateFailed",
                "can_retry": True,
                "retry_after": 0,
            },
        },
    )
    assert widget.retry.isEnabled()
    widget.retry.click()
    assert commands[-1].request["@type"] == "resendMessages"
    assert commands[-1].request["message_ids"] == [10]
    count = len(commands)
    for state in ("connectionStateConnecting", "connectionStateReady"):
        widget.handle_event(
            RuntimeEvent(
                RuntimeEventKind.UPDATE,
                "updateConnectionState",
                {
                    "@type": "updateConnectionState",
                    "state": {"@type": state},
                },
            )
        )
    assert len(commands) == count


def test_large_history_and_accessible_controls(qtbot: QtBot) -> None:
    widget, commands = setup_chat(qtbot)
    messages: list[JsonObject] = [
        {
            "id": identifier,
            "chat_id": 1,
            "content": {
                "@type": "messageText",
                "text": {"text": f"Message {identifier}"},
            },
        }
        for identifier in range(1, 2001)
    ]
    response(widget, commands[-1], {"@type": "messages", "messages": messages})
    assert "Message 1" in widget.history.toPlainText()
    assert "Message 2000" in widget.history.toPlainText()
    for control in (
        widget.composer,
        widget.search,
        widget.chat_filter,
        widget.history,
        widget.chats,
    ):
        assert control.accessibleName()
