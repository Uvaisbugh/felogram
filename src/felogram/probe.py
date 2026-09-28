from __future__ import annotations

import json
import threading

from felogram.telegram.runtime import RuntimeEvent, RuntimeEventKind, TdRuntime
from felogram.telegram.tdjson_adapter import TdjsonTransport


def main() -> int:
    transport = TdjsonTransport()
    response = transport.execute(
        {"@type": "getTextEntities", "text": "Felogram https://telegram.org"}
    )
    if response is None:
        raise RuntimeError("TDLib returned no response to the native probe")
    print("TDLib native probe succeeded")
    print(json.dumps(response, indent=2, ensure_ascii=False))

    stop_requested = threading.Event()
    events: list[RuntimeEvent] = []

    def capture(event: RuntimeEvent) -> None:
        events.append(event)
        print(f"{event.kind}: {event.message}")
        if (
            event.kind == RuntimeEventKind.AUTHORIZATION
            and event.message == "authorizationStateWaitTdlibParameters"
        ):
            stop_requested.set()

    timeout = threading.Timer(5.0, stop_requested.set)
    timeout.daemon = True
    timeout.start()
    try:
        TdRuntime(transport).run(stop_requested, capture)
    finally:
        timeout.cancel()

    required = {
        RuntimeEventKind.VERSION,
        RuntimeEventKind.AUTHORIZATION,
        RuntimeEventKind.STOPPED,
    }
    observed = {event.kind for event in events}
    if not required <= observed or any(event.kind == RuntimeEventKind.ERROR for event in events):
        raise RuntimeError("TDLib lifecycle probe did not complete successfully")
    if events[-1].message != "TDLib closed cleanly":
        raise RuntimeError("TDLib lifecycle probe did not close cleanly")
    return 0
