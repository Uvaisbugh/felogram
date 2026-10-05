# Felogram

**Telegram for developers.** An independent Windows desktop client built with Python, PySide6, and TDLib.

This repository contains the **experimental Python prototype**. The production
direction targets native Windows and Android clients on mature upstream foundations.
See the [client comparison](docs/CLIENT_RESEARCH.md), [revised product plan](docs/PRODUCT_PLAN.md),
and separate [Android foundation](https://github.com/Uvaisbugh/felogram-android).
The proposed native products have not shipped Felogram binaries yet.

## Early alpha

Implemented: responsive desktop UI, account authorization screens, persistent sessions with a Windows DPAPI-protected database key, and local code-snippet clipboard export.

The chat tab loads main-list chats and paginated history, with updates, edits,
deletions, text sending, and native code-block messages. Failed-message retries
reuse TDLib's existing message ID; there is no automatic resend on reconnect.
Message search, saved searches, local collections, and unread filters are available.
These features have automated coverage and still need live-account verification.
Standalone snippets export Markdown text; another client's paste behavior may differ.
Felogram is not affiliated with Telegram.

## Run from source

Requires Windows, Python 3.14, and uv.

```powershell
uv sync --locked --group dev
uv run felogram-probe
uv run felogram
```

Get your own application credentials at [my.telegram.org](https://my.telegram.org/) and enter them in the app. Optional environment variables are listed in `.env.example`; the app does not automatically load that file. Never commit credentials or session data.

The optional **Remember API credentials securely** checkbox stores them with
Windows DPAPI and configures TDLib on reopening. Login codes and two-step passwords
are not saved. Uncheck it on the API screen and continue to remove saved API credentials.

Sessions live under `%LOCALAPPDATA%\Felogram`. Closing preserves login. DPAPI protects the database key for the Windows user; ordinary Telegram cloud chats are not end-to-end encrypted.

Saved searches and collections are local, DPAPI-protected preferences. Unsent drafts
are kept in memory while switching chats; they are not restored after restart.

## Developer controls

- `Ctrl+K`: filter chats; arrow keys select a chat.
- `Ctrl+F`: search messages; `Alt+Left`: return to history.
- `Ctrl+L`: focus the draft; `Ctrl+Enter`: send.
- `F1`: shortcut help.

Enable **Send as code** and enter a language to send a native code block. Use the
code-block selector and **Copy code** to copy code from visible messages.
To make a local collection, select a chat, type a name in the collection field,
and click **Add chat**. The unread filter uses TDLib's reported unread count;
this alpha does not automatically mark viewed messages as read.

For a local Windows executable, see [packaging verification](docs/PACKAGING.md).

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
