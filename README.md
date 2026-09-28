# Felogram

A desktop Telegram client built with Python, PySide6, and TDLib, with room to
grow into a workspace for messaging, search, and user-controlled automation.

## Current status

The initial research and Windows environment assessment are complete. The first
implementation milestone provides a minimal desktop window and a TDLib runtime
probe.

- [Research, architecture, and setup plan](docs/RESEARCH_AND_SETUP.md)
- [Initial architecture decision](docs/adr/001-desktop-foundation.md)

Install and verify the project:

```powershell
uv sync --group dev
uv run pytest
uv run felogram-probe
uv run felogram
```

`felogram-probe` checks the native TDLib binding without opening the desktop UI.
`felogram` opens the desktop window, starts TDLib on a background worker, reports
its version and initial authorization state, and closes the native client before
the process exits. Telegram account login follows in a separate milestone.

The product name is **Felogram** and the Python package name is `felogram`. The
existing workspace directory, `telgramRX`, can remain as it is.
