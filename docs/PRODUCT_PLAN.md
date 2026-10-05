# Felogram product plan

Name: **Felogram**. Tagline: **Telegram for developers.** Keep the established package and session names consistent. The name is a project choice, not a trademark or registry availability claim.

Serve developers and technical communities discussing code, following channels, and moving between support groups and focused conversations.

## Principles

Reliable messaging first. Keyboard-accessible workflows. Local credentials. Never execute pasted code. Explicit, opt-in automation. Honest feature claims and approachable contributions.

## Roadmap

| Milestone | Scope | Acceptance gate |
| --- | --- | --- |
| 0.1 foundation alpha | Login flow, responsive shutdown, local snippets, open-source docs and CI | Checks pass; source setup documented; manual login status disclosed |
| 0.2 messaging | Chat list, history, text send, pagination and reconnect | Two accounts exchange messages; retry avoids duplicates; shutdown verified |
| 0.3 developer conversations | TDLib code entities, syntax display, keyboard navigation and search | Code round trips correctly; shortcuts and search verified |
| 0.4 workspaces | Local chat collections, unread filters and saved searches | Organization persists without unexpected server changes |
| Later integrations | User-triggered project links and approved automation | Permissions, preview, cancellation and failures defined first |

The implemented snippet tool works offline, before login, and copies Markdown without sending it. Native Telegram formatting belongs in the messaging milestone.

## Architecture and next task

Keep product logic in `application`, native protocol and receive-loop ownership in `telegram`, and widgets in `ui`. TDLib owns synchronization; keep native calls off the UI thread.

Next: add correlated chat/history responses and ordered chat updates, then a chat list and read-only history. Add sending after read-path and authorization-transition tests.

Initial exclusions: arbitrary plugins, bulk messaging, automatic code execution, hosted credentials, and cross-platform claims. Windows remains the supported platform because key storage uses DPAPI.
