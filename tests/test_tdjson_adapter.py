from __future__ import annotations

import pytest

from felogram.telegram.tdjson_adapter import TdjsonProtocolError, decode_tdjson


def test_decode_tdjson_accepts_an_object() -> None:
    assert decode_tdjson(b'{"@type":"ok"}') == {"@type": "ok"}


@pytest.mark.parametrize("payload", [b"not-json", b"[]"])
def test_decode_tdjson_rejects_invalid_payloads(payload: bytes) -> None:
    with pytest.raises(TdjsonProtocolError):
        decode_tdjson(payload)
