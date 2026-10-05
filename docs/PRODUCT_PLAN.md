# Felogram product plan

Felogram: **Telegram, organized for focused work.** An independent open-source
client for developers and power users, with complete everyday messaging as its
foundation. Windows and Android are separate native products. The name is kept
for continuity; trademark clearance is not established.

## Why use it

Technical communities scatter useful conversations, code, files and release
announcements across chats. Felogram should make returning to that work fast
while preserving familiar Telegram behavior.

| Journey | Windows proposal | Android proposal | Acceptance evidence |
| --- | --- | --- | --- |
| Follow a project across support, team and release chats | Project workspaces, local bookmarks and saved searches | Compact workspace switcher and bookmarks | Find a saved discussion in three actions after restarting |
| Help debug a problem | Exact code copy, safe text/log attachment preview and return to discussion | Code copy/wrapping and reliable file sharing | Unicode and formatting preserved; no code execution; binary fallback |
| Keep several conversations open | Command palette, keyboard navigation, independent conversation windows | Quick recent-chat navigation and predictable back behavior | No draft loss or send to the wrong recipient during switching |
| Follow busy communities without losing focus | Local focus profiles and notification controls | Notification channels and local quiet periods | Selected notifications arrive; read receipts remain correct |
| Find a past fix/file | Chat/sender/date/type filters and reusable searches | Touch-friendly filters and jump-to-message | Results link to correct account, chat and message |

These are proposed features, not claims about the existing executable. Start
with local, account-scoped organization. Shared concepts do not imply automatic
cross-device synchronization; design explicit export/import without secrets later.

## Everyday baseline

Preserve and verify upstream login, multiple accounts, text/edit/reply/forward,
reactions, folders/topics, media/files, voice messages, calls where supported
upstream, notifications, search, drafts and reconnect. Document upstream platform
differences rather than promising identical features everywhere.

Windows: resizable layout, keyboard access, screen readers, high DPI/multiple
monitors, predictable tray behavior, safe file opening, sleep/resume and a tested
install/update/uninstall path.

Android: readable touch UI, share intents, TalkBack, font scaling, process
recreation, notification reliability under background limits, battery measurement,
media permissions and clear Play/FOSS build differences.

## Foundations and repositories

- [felogram](https://github.com/Uvaisbugh/felogram): existing MIT Python/TDLib
  Windows R&D prototype and research. Published alpha is experimental.
- [felogram-android](https://github.com/Uvaisbugh/felogram-android): separate
  official Android source fork retaining upstream history/license. No Felogram APK yet.
- Windows production candidate: official Telegram Desktop C++/Qt fork. Prove
  its build first, then establish a dedicated native repository. Preserve this
  prototype's history/license instead of importing GPL code into its MIT tree.

See [research](CLIENT_RESEARCH.md) and [foundation decision](adr/002-production-platform-foundations.md).

## Delivery sequence

| Stage | Output | Acceptance gate |
| --- | --- | --- |
| 0: reproducible foundations | Pinned source, toolchain manifests, baseline builds, license inventory | Unmodified Windows executable/Android debug APK build; startup evidence recorded |
| 1: identity | Felogram names/icons/package/storage identity, credentials setup, source links | Install beside official clients; login/reopen/logout on test accounts |
| 2: everyday alpha | Verified messaging, media, accounts, notifications and reconnect | Two-account/device matrix passes; compatibility/limitations published |
| 3: distinctive release | Local workspaces, bookmarks, exact code copy, reusable searches | Five journeys above pass with users; preference migration and upstream merge tested |
| 4: public beta | Measured performance/accessibility, signed artifacts and updates | Corresponding source, clean-machine install/upgrade/uninstall and account-isolation checks |
| 5: stable | Repeated upstream update rehearsals and resolved blockers | Regression gates pass; release maintenance owner and response process documented |

Implement one differentiator at a time. Maintain a patch inventory with rationale,
tests, migration behavior and upstream conflicts. Keep protocol/storage changes small.

## Quality targets, not achieved results

- Startup and idle memory within 15% of the same upstream build on identical
  hardware/data, unless a measured usability tradeoff is accepted.
- Scroll/search a 10,000-message fixture without freezes; record frame times.
- Delivery/edit/retry preserves text, code and files without duplicates across
  network interruption, restart and account switching.
- Android background notifications pass screen-off, process recreation and
  battery restrictions on at least two vendor devices before beta.
- Keyboard/TalkBack, 200% text scaling and high contrast pass with actual users.
- Opt-in testing measures crash-free sessions without collecting message contents;
  synthetic tests do not establish a production crash rate.

Publish methods, device/OS/build versions and known failures. No universal best
claim without evidence.

## Scope limits

First release excludes arbitrary plugins, bulk automation, executed snippets,
automatic external AI processing and a new synchronization backend. Translation
needs provider/data disclosure before adoption. Preserve upstream communication
semantics and sponsored messages. No added telemetry by default; user-triggered
diagnostics must be checked for secrets. Release signing secrets stay outside source.
