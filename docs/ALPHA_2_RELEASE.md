# Felogram v0.1.0-alpha.2

## Developer messaging

- Text sending with delivery status and explicit retries using failed message IDs.
- Native Telegram code-block messages, labeled display, and code-copy controls.
- Paginated message search and local saved searches.
- Local collections, title filtering, and unread filtering.
- Keyboard shortcuts with discoverable help.
- Optional DPAPI-protected API credentials for reopening, and encrypted
  preferences isolated by Telegram account ID.

## Verification

41 automated tests, Ruff lint/format, strict mypy, native TDLib schema parsing,
real Windows encryption, and source desktop startup/shutdown passed locally.
A one-folder executable also passed local native and desktop probes after fixing
DLL discovery. A manually dispatched packaging workflow tests on a fresh Windows
runner without publishing binary artifacts.

## Alpha limitations

Live account login, message exchange, and session reopening remain unverified.
Secret-chat search, media rendering, forum-topic selection, and automatic updates
are unavailable. Drafts are kept in memory only. Sends are never automatically
repeated after reconnect or restart. Only TDLib-confirmed retryable failed
messages can use Retry; uncertain delivery stays blocked pending a status check.
Unread filtering does not mark messages as read. No downloadable binary is
attached: complete native dependency notices and end-user checks remain release gates.
