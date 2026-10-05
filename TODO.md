# Felogram to-do list

## 1. Run on this PC

- [x] Verify lint, formatting, types, and automated tests: 41 tests passed.
- [x] Verify the locked installation with `uv sync --locked --group dev`.
- [x] Run the installed `felogram-probe` entry point: TDLib 1.8.67 closes cleanly.
- [x] Launch Felogram on this PC; account and snippet behavior verified by Qt tests.
- [ ] Create personal Telegram API credentials at https://my.telegram.org/.
- [ ] Sign in manually and verify the required authorization screens.
- [ ] Close and reopen the app to confirm session persistence.
- [x] Verify clipboard export and embedded backticks through automated tests.
- [x] Record local versions in `docs/RD_MESSAGING.md`; native startup passes.

## 2. Publish the repository

- [x] Add MIT license, README, contributor guide, security policy, and Windows CI.
- [x] Restore and verify GitHub authentication for Uvaisbugh.
- [x] Review tracked source and history; no real credentials identified.
- [x] License original project source under MIT and inspect runtime license metadata.
- [x] Check repository-name availability under Uvaisbugh.
- [x] Create https://github.com/Uvaisbugh/felogram and configure origin.
- [x] Commit and push the reviewed source to the public repository.
- [x] Confirm the Windows workflow passes on GitHub (run 37286548316).
- [x] Enable private vulnerability reporting.
- [x] Protect the default branch with required Windows checks.
- [x] Add repository description, topics, milestone, and issues #1–#3.
- [x] Publish v0.1.0-alpha.1 with clear limitations: read-only chats are
  experimental, sending is unavailable, and live login is not yet verified.
- [ ] Verify packaging and dependency redistribution requirements before
  distributing desktop binaries.

## 3. Research and development

### First priority: usable messaging

- [x] Research TDLib chat-list loading, chat ordering, and update handling.
- [x] Add correlated responses and ordered update events; domain-specific typed models remain future work.
- [x] Implement an experimental main chat list and read-only message history.
- [x] Add history pagination, connection status, and manual retry after history errors.
- [x] Implement text sending with duplicate-safe retries of TDLib's failed message ID.
- [ ] Verify message exchange with two test accounts, reconnect, and shutdown.

### Developer experience

- [x] Research native code entities and sending requirements; record the next gate in `docs/RD_MESSAGING.md`.
- [x] Add native code messages, code display, language labels, and code-copy actions.
- [x] Add keyboard navigation, focus shortcuts, and F1 shortcut discovery.
- [x] Add paginated message search and encrypted, account-specific saved searches.
- [x] Verify accessible control labels and a 2,000-message synthetic history.
- [ ] Verify assistive technology and real technical-group workflows with signed-in accounts.

### Later research

- [x] Prototype encrypted, account-specific local collections and unread filters.
- [x] Investigate integration permission boundaries in `docs/RD_NEXT.md`.
- [x] Build and smoke-test a local Windows executable; fix DLL search-path contamination.
- [ ] Verify the Windows bundle on a fresh CI runner.
- [x] Define update-distribution gates and portable secure-storage requirements in `docs/RD_NEXT.md`.

## Remaining external verification

Personal Telegram credentials and sign-in must be entered in the app. Live
two-account message exchange, session reopening, and assistive-technology checks
remain manual. No public executable or installer is released until the native
dependency notices and end-user verification are complete.

Follow [the product plan](docs/PRODUCT_PLAN.md) for milestone acceptance gates
and [the release checklist](docs/RELEASING.md) before publication.
