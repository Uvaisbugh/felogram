# Messaging research and implementation

Research date: 2026-10-05. Local baseline: Windows 11 build 26300,
Python 3.14.7, PySide6 6.11.2, TDLib 1.8.67.

## Decisions grounded in TDLib documentation

- Use `loadChats` and chat updates to maintain the main chat list. Sort by
  descending `(order, chat_id)`; order zero removes a chat from that list.
- Use `getChatHistory` with `from_message_id=0` for recent history and the oldest
  loaded ID for earlier pages. Deduplicate message IDs because boundaries overlap.
  A short page does not necessarily mean history has ended.
- Correlate each request using `@extra`. Include selection generation in the
  history operation so replies for previous selections are ignored.
- Display remote text as plain text, and placeholders for unsupported media.
- Preserve ordered new-message, content-edit, and deletion updates.

Implemented: read-only chat preview, correlated response events, update forwarding,
pagination with a no-progress guard, retry after history errors, connection status,
and clearing private display data on authorization loss.

Sources: [TDLib getting started](https://core.telegram.org/tdlib/getting-started),
[getChatHistory](https://core.telegram.org/tdlib/docs/classtd_1_1td__api_1_1get_chat_history.html),
[getChats guidance](https://core.telegram.org/tdlib/docs/classtd_1_1td__api_1_1get_chats.html).

## Sending and native code formatting: next gate

`sendMessage` takes an `inputMessageText` with `formattedText`. Use TDLib text
entities for native code blocks; copying Markdown is not equivalent. Pin schema
validation to the installed TDLib release; online documentation may describe a
newer schema. Track temporary message IDs and success/failure updates. Do not
automatically submit a second send when delivery is uncertain. Validate text
length against the account's TDLib option, support draft recovery, and surface
permission or network failures before enabling sending.

Sources: [sendMessage](https://core.telegram.org/tdlib/docs/classtd_1_1td__api_1_1send_message.html),
[inputMessageText](https://core.telegram.org/tdlib/docs/classtd_1_1td__api_1_1input_message_text.html).

## Follow-up experiments

1. Test the preview on two consenting test accounts, including reconnect and
   rapid switching. Validate archive/moved chats, very large histories and edits.
2. Move chat storage into a presentation-neutral model and batch UI updates before
   scaling large lists. Current widgets rebuild the visible list on chat changes.
3. Research message search request schemas and keyboard navigation after the
   live read path passes. Add local collections only when their persistence model
   is defined. Integrations and other platforms remain future milestones.
4. Build a one-folder Windows package; test native discovery and licenses, then
   verify it on a clean machine before distributing it.

No real-account messaging or clean-machine packaging is claimed as verified.
