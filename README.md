# Felogram

**Telegram for developers.** An independent Windows desktop client built with Python, PySide6, and TDLib.

## Early alpha

Implemented: responsive desktop UI, account authorization screens, persistent sessions with a Windows DPAPI-protected database key, and local code-snippet clipboard export.

An experimental read-only chat tab now loads the main chat list and paginated
history, with message updates, edits, and deletions. It has automated coverage
but still needs live-account verification. **Message sending is not implemented.**
Snippets export Markdown text; another client's paste behavior may differ.
Felogram is not affiliated with Telegram.

## Run from source

Requires Windows, Python 3.14, and uv.

```powershell
uv sync --locked --group dev
uv run felogram-probe
uv run felogram
```

Get your own application credentials at [my.telegram.org](https://my.telegram.org/) and enter them in the app. Optional environment variables are listed in `.env.example`; the app does not automatically load that file. Never commit credentials or session data.

Sessions live under `%LOCALAPPDATA%\Felogram`. Closing preserves login. DPAPI protects the database key for the Windows user; ordinary Telegram cloud chats are not end-to-end encrypted.

## Contribute

Read the [product plan](docs/PRODUCT_PLAN.md), [contributor guide](CONTRIBUTING.md), [security policy](SECURITY.md), and [release checklist](docs/RELEASING.md).

```powershell
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
```

See the [architecture decision](docs/adr/001-desktop-foundation.md) and [research notes](docs/RESEARCH_AND_SETUP.md).

Original source is available under the [MIT license](LICENSE). Dependencies retain their own licenses; review redistribution obligations before bundling binaries.
