# Felogram to-do list

## 1. Run on this PC

- [x] Verify lint, formatting, types, and automated tests: 23 tests passed.
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
- [ ] Publish a source alpha with clear limitations: read-only chats are
  experimental, sending is unavailable, and live login is not yet verified.
- [ ] Verify packaging and dependency redistribution requirements before
  distributing desktop binaries.

## 3. Research and development

### First priority: usable messaging

- [x] Research TDLib chat-list loading, chat ordering, and update handling.
- [x] Add correlated responses and ordered update events; domain-specific typed models remain future work.
- [x] Implement an experimental main chat list and read-only message history.
- [x] Add history pagination, connection status, and manual retry after history errors.
- [ ] Implement text sending with duplicate-safe retry behavior.
- [ ] Verify message exchange with two test accounts, reconnect, and shutdown.

### Developer experience

- [x] Research native code entities and sending requirements; record the next gate in `docs/RD_MESSAGING.md`.
- [ ] Add code display, language labels, and code-copy actions.
- [ ] Define keyboard navigation and shortcut discovery.
- [ ] Add message search and saved searches.
- [ ] Validate accessibility, large histories, and technical group workflows.

### Later research

- [ ] Prototype local chat collections and unread filters.
- [ ] Investigate user-triggered project integrations with explicit permissions.
- [ ] Evaluate clean-machine Windows packaging and update distribution.
- [ ] Evaluate portable secure key storage before considering other platforms.

Follow [the product plan](docs/PRODUCT_PLAN.md) for milestone acceptance gates
and [the release checklist](docs/RELEASING.md) before publication.
