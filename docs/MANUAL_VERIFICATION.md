# Live account verification

Use your own credentials in Felogram's Telegram account tab, never in an issue.
The local executable is `dist/local/Felogram/Felogram.exe`; keep its `_internal` folder.

## Account and session

1. Obtain an API ID and hash from my.telegram.org and enter them in the app.
2. Optionally select secure API-credential storage, then finish the phone/code
   and any two-step authentication requested by Telegram.
3. Confirm the Chats tab loads your main chat list and history.
4. Close the app normally, reopen it, and confirm the account session persists.
   Reenter API credentials if you did not choose to remember them.

## Two-account exchange

Use two consenting test accounts and explicitly select their test conversation.
Confirm the recipient above the draft before pressing Send.

1. Send a short text, then a code block with a language label and an emoji.
2. Confirm the other account receives both and copies the exact code.
3. Reply from the second account; check new messages, edits, and deletions.
4. Switch chats rapidly while loading history; verify no mixed conversations.
5. Disconnect and reconnect the network. Confirm existing pending sends resolve
   without duplicate submissions. Use Retry only for a confirmed retryable failure.
6. Search a known term, load another page, save the query, and reopen the app.
7. Add a local collection and check unread filtering without changing server folders.

## Desktop and accessibility

Verify Tab/Shift+Tab, arrow keys, Ctrl+K, Ctrl+F, Ctrl+L, Ctrl+Enter, Alt+Left,
and F1. Test with Windows Narrator, high contrast, and display scaling.
Synthetic large-history tests are automated; real high-traffic groups still
need manual observation for responsiveness and update ordering.

Record OS/app version, pass/fail results, and sanitized error categories. Never
attach login credentials, account IDs, session databases, or private chat contents.
