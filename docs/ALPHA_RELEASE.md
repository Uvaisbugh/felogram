# Felogram v0.1.0-alpha.1

Telegram for developers: the first public source alpha for Windows.

## Included

- Python/PySide6 desktop foundation and TDLib 1.8.67 integration.
- Account authorization screens and DPAPI-protected session key storage.
- Local code-snippet formatting and clipboard export.
- Experimental main chat list and read-only history, including pagination,
  chat ordering, edits/deletions, and stale-response protection.
- MIT source license, contribution guidance, security reporting, and Windows CI.

## Verification

Locked installation, native TDLib version/lifecycle probe, desktop launch,
23 automated tests, Ruff lint/format, and strict mypy passed on Windows 11
build 26300 with Python 3.14.7. Hosted Windows checks passed before tagging.

## Limitations

Real Telegram account login and read-only chat behavior are not yet manually
verified. Message sending, native code formatting, media rendering, search,
and workspaces are not available. Clipboard export produces Markdown text.
This release contains source only; no installer or verified desktop binary.

Run instructions are in the README. Development milestones and remaining
verification tasks are in TODO.md and repository issues.
