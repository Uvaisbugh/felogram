from __future__ import annotations

import time
from dataclasses import dataclass
from html import escape
from uuid import uuid4

from felogram.telegram.runtime import RuntimeCommand
from felogram.telegram.transport import JsonObject, JsonValue


def utf16_length(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


def send_text(
    chat_id: int, text: str, *, limit: int = 4096, language: str | None = None
) -> JsonObject:
    if not text.strip():
        raise ValueError("Write a message first.")
    length = utf16_length(text)
    if length > limit:
        raise ValueError(f"Message exceeds the {limit}-character limit.")
    entities: list[JsonValue] = []
    if language is not None:
        if len(language) > 64 or any(character in language for character in "\r\n"):
            raise ValueError("Use a short, single-line language name.")
        entities.append(
            {
                "@type": "textEntity",
                "offset": 0,
                "length": length,
                "type": {"@type": "textEntityTypePreCode", "language": language.strip()},
            }
        )
    return {
        "@type": "sendMessage",
        "chat_id": chat_id,
        "topic_id": None,
        "reply_to": None,
        "options": {"@type": "messageSendOptions", "paid_message_star_count": 0},
        "reply_markup": None,
        "input_message_content": {
            "@type": "inputMessageText",
            "text": {"@type": "formattedText", "text": text, "entities": entities},
            "link_preview_options": {"@type": "linkPreviewOptions", "is_disabled": True},
            "clear_draft": False,
        },
    }


@dataclass
class SendAttempt:
    chat_id: int
    operation: str
    message_id: int | None = None
    state: str = "requesting"
    retry_at: float = 0.0
    can_retry: bool = False


class Outbox:
    """Allow one tracked send; retries reuse TDLib's failed message ID."""

    def __init__(self) -> None:
        self.attempt: SendAttempt | None = None

    def start(self, chat_id: int, request: JsonObject) -> RuntimeCommand:
        if self.attempt is not None:
            raise ValueError("Wait for the current message's delivery status before sending again.")
        operation = f"Send:{uuid4()}"
        self.attempt = SendAttempt(chat_id, operation)
        return RuntimeCommand(operation, request)

    def accept(self, message: JsonObject) -> None:
        attempt = self.attempt
        if attempt is None or message.get("chat_id") != attempt.chat_id:
            return
        identifier = message.get("id")
        if not isinstance(identifier, int):
            return
        attempt.message_id = identifier
        state = message.get("sending_state")
        if not isinstance(state, dict):
            self.attempt = None
        elif state.get("@type") == "messageSendingStateFailed":
            attempt.state = "failed"
            attempt.can_retry = state.get("can_retry") is True and not any(
                state.get(key)
                for key in (
                    "need_another_sender",
                    "need_another_reply_quote",
                    "need_drop_reply",
                    "required_paid_message_star_count",
                )
            )
            delay = state.get("retry_after", 0)
            attempt.retry_at = time.monotonic() + (
                max(0.0, float(delay)) if isinstance(delay, (float, int)) else 0
            )
        else:
            attempt.state = "pending"

    def retry(self) -> RuntimeCommand:
        attempt = self.attempt
        if (
            attempt is None
            or attempt.state != "failed"
            or not attempt.can_retry
            or attempt.message_id is None
            or time.monotonic() < attempt.retry_at
        ):
            raise ValueError("This message cannot be retried yet.")
        attempt.operation = f"Retry:{uuid4()}"
        attempt.state = "requesting"
        return RuntimeCommand(
            attempt.operation,
            {
                "@type": "resendMessages",
                "chat_id": attempt.chat_id,
                "message_ids": [attempt.message_id],
                "quote": None,
                "paid_message_star_count": 0,
            },
        )


@dataclass(frozen=True)
class CodeBlock:
    language: str
    text: str


def formatted_content(message: JsonObject) -> JsonObject:
    content = message.get("content")
    if isinstance(content, dict):
        formatted = content.get("text") or content.get("caption")
        if isinstance(formatted, dict):
            return formatted
        return {"text": f"[{content.get('@type', 'Unsupported message')}]"}
    return {"text": "[Unsupported message]"}


def code_blocks(formatted: JsonObject) -> list[tuple[int, int, CodeBlock]]:
    text = formatted.get("text")
    entities = formatted.get("entities")
    if not isinstance(text, str) or not isinstance(entities, list):
        return []
    encoded = text.encode("utf-16-le")
    result: list[tuple[int, int, CodeBlock]] = []
    for entity in entities:
        if not isinstance(entity, dict):
            continue
        kind = entity.get("type")
        offset, length = entity.get("offset"), entity.get("length")
        if (
            not isinstance(kind, dict)
            or kind.get("@type")
            not in {"textEntityTypeCode", "textEntityTypePre", "textEntityTypePreCode"}
            or not isinstance(offset, int)
            or not isinstance(length, int)
            or offset < 0
            or length <= 0
            or (offset + length) * 2 > len(encoded)
        ):
            continue
        try:
            start = len(encoded[: offset * 2].decode("utf-16-le"))
            code = encoded[offset * 2 : (offset + length) * 2].decode("utf-16-le")
        except UnicodeDecodeError:
            continue
        result.append((start, start + len(code), CodeBlock(str(kind.get("language", "")), code)))
    return sorted(result, key=lambda value: value[0])


def render_content(formatted: JsonObject) -> str:
    value = formatted.get("text", "")
    text = value if isinstance(value, str) else ""
    parts: list[str] = []
    cursor = 0
    for start, end, block in code_blocks(formatted):
        if start < cursor:
            continue
        parts.append(escape(text[cursor:start]).replace("\n", "<br>"))
        parts.append(
            f"<p><small>{escape(block.language or 'code')}</small></p>"
            f"<pre style='background-color:#20252d;color:#eeeeee;padding:8px;'>"
            f"{escape(block.text)}</pre>"
        )
        cursor = end
    parts.append(escape(text[cursor:]).replace("\n", "<br>"))
    return "".join(parts)
