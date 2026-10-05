# First source release

1. Review tracked files and Git history for credentials, sessions, and private data. Ignoring files does not remove old commits.
2. Confirm authority to license contributed source under MIT.
3. Create a public repository named `felogram` and connect its Git remote. Description: Telegram for developers — a Python desktop client powered by TDLib.
4. Enable private vulnerability reporting and default-branch protection using Windows checks.
5. Push reviewed source and verify hosted CI.
6. Manually verify login and session reopening; record tested Windows and Python versions.
7. Tag a source alpha after checks pass. Disclose experimental read-only chats,
   missing sending, and unverified live login. Do not upload untested binaries.

Binary releases require clean-machine startup, native loading, shutdown, installation/session checks, and bundled dependency license notices.
