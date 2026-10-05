# Remaining research decisions

Date: 2026-10-05.

## Local organization and privacy

Collections and saved searches are application-owned settings. They do not
modify Telegram folders or chat state. Persist them under the Windows user's
Felogram directory in a DPAPI-protected file. Keep unsent message drafts in memory
for this alpha; do not describe them as restart-persistent. The first prototype
supports one active account; preference files are selected by TDLib's account ID.
Concurrent multi-account support remains unimplemented.

## Project integrations

The first integration should be user-triggered links to project resources, with
no account credentials or background actions. A later connector needs explicit
permissions, a preview of outgoing content, cancellation, and error handling.
Do not automatically fetch every URL shared in a chat or execute embedded code.
Keep this as a design decision until an actual connector use case is selected.

## Other platforms and secure storage

Current security imports and protection are Windows-specific. A portable design
needs a protected-bytes interface implemented separately for macOS Keychain and
Linux Secret Service. Unsupported or locked stores should produce an actionable
error, with no plaintext fallback. Evaluate packaging on each OS before changing
the declared support matrix. No additional platform is supported by this alpha.

## Windows package and updates

Use a one-folder PyInstaller build first so native libraries and notices can be
inspected. Verify native TDLib loading and responsive desktop shutdown outside
the source environment. Then run the same bundle on a fresh Windows CI runner.
Keep automatic updates out of scope until release signing, update provenance,
rollback, and data migration are defined. Rebuilding is the current update path.

## Release gates

Record automated tests separately from live account tests. An unauthenticated
smoke test does not prove login, delivery, or session reopening. A local bundle
is not a clean-machine installer. Do not publish a binary until its complete
native dependency notices and end-user verification are reviewed.
