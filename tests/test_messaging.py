from __future__ import annotations

import time

import pytest

from felogram.application.messaging import Outbox, code_blocks, render_content, send_text
from felogram.telegram.tdjson_adapter import TdjsonTransport
from felogram.telegram.transport import JsonObject


def failed_message(*, retry_after: float = 0, paid: int = 0) -> JsonObject:
    return {
        "@type": "message",
        "id": 50,
        "chat_id": 1,
        "sending_state": {
            "@type": "messageSendingStateFailed",
            "can_retry": True,
            "retry_after": retry_after,
            "required_paid_message_star_count": paid,
        },
    }


def test_code_entity_uses_utf16_and_preserves_literal_content() -> None:
    request = send_text(1, "😀<tag>\n", language="python")
    content = request["input_message_content"]
    assert isinstance(content, dict)
    formatted = content["text"]
    assert isinstance(formatted, dict)
    assert formatted["entities"] == [
        {
            "@type": "textEntity",
            "offset": 0,
            "length": 8,
            "type": {"@type": "textEntityTypePreCode", "language": "python"},
        }
    ]
    block = code_blocks(formatted)[0][2]
    assert block.text == "😀<tag>\n"
    assert "&lt;tag&gt;" in render_content(formatted)
    assert "<tag>" not in render_content(formatted)


def test_code_entity_after_emoji_is_extracted_correctly() -> None:
    formatted: JsonObject = {
        "text": "😀 code",
        "entities": [
            {
                "offset": 3,
                "length": 4,
                "type": {"@type": "textEntityTypeCode"},
            }
        ],
    }
    assert code_blocks(formatted)[0][2].text == "code"


@pytest.mark.parametrize("text", [" ", "😀😀😀"])
def test_empty_and_overlength_messages_are_rejected(text: str) -> None:
    with pytest.raises(ValueError):
        send_text(1, text, limit=4)


def test_outbox_blocks_double_submit_and_retries_existing_id() -> None:
    outbox = Outbox()
    outbox.start(1, send_text(1, "hello"))
    with pytest.raises(ValueError):
        outbox.start(1, send_text(1, "hello"))
    outbox.accept(failed_message(retry_after=10))
    with pytest.raises(ValueError):
        outbox.retry()
    assert outbox.attempt is not None
    outbox.attempt.retry_at = time.monotonic() - 1
    retry = outbox.retry()
    assert retry.request["@type"] == "resendMessages"
    assert retry.request["message_ids"] == [50]
    with pytest.raises(ValueError):
        outbox.retry()
    outbox.accept({"@type": "message", "chat_id": 1, "id": 60, "sending_state": None})
    assert outbox.attempt is None


def test_outbox_does_not_pay_or_retry_another_chat() -> None:
    outbox = Outbox()
    outbox.start(1, send_text(1, "hello"))
    outbox.accept({"@type": "message", "chat_id": 2, "id": 60})
    assert outbox.attempt is not None
    outbox.accept(failed_message(paid=1))
    with pytest.raises(ValueError):
        outbox.retry()


@pytest.mark.native
def test_installed_native_parser_accepts_send_schema_without_sending() -> None:
    # execute cannot send messages. This checks parsing without network side effects.
    response = TdjsonTransport().execute(send_text(1, "test 😀", language="python"))
    assert response is not None
    assert response["@type"] == "error"
    assert "synchronously" in str(response.get("message", ""))
