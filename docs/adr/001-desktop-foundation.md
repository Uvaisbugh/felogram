# ADR-001: Desktop foundation

Date: 2026-09-28

Status: Accepted and implemented.

## Context

Felogram starts as a Windows desktop Telegram client. The existing machine has
CPython 3.14.7 and a native C++ toolchain. The first deliverable needs only a
responsive window and a verified TDLib lifecycle. Future messaging, workspaces,
search, and integrations should share an application core.

## Decision

- Use CPython 3.14.7, PySide6 6.11.2, and `tdjson` 1.8.67.
- Start with Qt Widgets and a narrow adapter around the modern TDLib JSON API.
- Host one receive loop in a dedicated worker, with queued commands and a Qt
  presentation bridge. Keep core logic independent of Qt.
- Use uv with a committed lockfile, Ruff, mypy, pytest, and pytest-qt.
- Leave Telegram persistence and synchronization with TDLib.
- Verify a Windows one-folder package early with PyInstaller.

## Alternatives and tradeoffs

| Alternative | Why it is not the initial choice |
| --- | --- |
| Direct ctypes and a self-built TDLib DLL | More native setup and packaging work; retain as a fallback if the packaged binding fails its verification. |
| QtAsyncio or qasync | QtAsyncio remains a technical preview; qasync's documented Python range excludes 3.14. The first TDLib loop needs neither. |
| Full Python TDLib framework | Adds framework and schema coupling; the evaluated candidates do not fit Windows as directly as the thin binding. |
| Telegram Desktop fork | Reuses a mature client but changes the project toward C++ and an existing product architecture. |
| Direct MTProto client | Moves protocol implementation and library selection into the critical path before the desktop foundation exists. |
| Electron or Tauri frontend | Adds another language/runtime boundary before there is a demonstrated UI requirement for it. |

The selected path depends on third-party native wheels and leaves request
tracking, domain conversion, and lifecycle handling with the project. The adapter
limits that dependency to one module. A failed native probe or unsupported target
platform should reopen this decision.

## Verification gate

Before promoting this ADR to implemented, demonstrate window startup, native
version response, ordered event delivery, responsive UI while receiving, and
graceful close. Record the actual package and runtime versions. Login and server
connectivity are separate acceptance criteria for the next milestone.

The gate passed on 2026-09-28 with CPython 3.14.7, PySide6 6.11.2, and TDLib
1.8.67. The following authentication milestone added the queued command path,
current TDLib authorization states, persistent session directories, and a
Windows DPAPI-protected database key. Live account authorization remains a
manual check because it requires user-owned Telegram credentials and codes.

See the [research and setup plan](../RESEARCH_AND_SETUP.md) for primary sources,
the environment inventory, exact setup sequence, and scope limits.
