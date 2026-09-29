# Felogram

A desktop Telegram client built with Python, PySide6, and TDLib, with room to
grow into a workspace for messaging, search, and user-controlled automation.

## Current status

The Windows desktop foundation and the first authentication flow are implemented.
Felogram presents the authorization step requested by TDLib and supports API
configuration, phone number, Telegram and email codes, registration, two-step
verification, and confirmation from another device.

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
its version, guides you through login, and closes the native client before the
process exits.

Before signing in, create Telegram application credentials at
[my.telegram.org](https://my.telegram.org/), then enter the API ID and API hash
inside Felogram. You can optionally prefill them with `TELEGRAM_API_ID` and
`TELEGRAM_API_HASH` environment variables. The API hash is removed from the input
after submission and is not logged.

TDLib session data is stored under `%LOCALAPPDATA%\Felogram`. Its database key is
randomly generated and protected for the current Windows user with DPAPI. Closing
Felogram preserves the session; it does not log the Telegram account out.

The automated suite verifies request schemas, response correlation, protected-key
persistence, UI state routing, native loading, responsive shutdown, and static
quality checks. A real account login still requires the user's own Telegram
credentials and code, so it is intentionally not automated.

The product name is **Felogram** and the Python package name is `felogram`. The
existing workspace directory, `telgramRX`, can remain as it is.
