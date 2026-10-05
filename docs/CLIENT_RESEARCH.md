# Client research and production direction

Reviewed 2026-10-05. This is source/documentation research, not a hands-on
performance, security or usability benchmark. Competitor features below are
not claims about the existing Felogram executable.

| Reference | Verified documentation | Lesson for Felogram |
| --- | --- | --- |
| [Nekogram source](https://github.com/Nekogram/Nekogram) and [site](https://nekogram.app/) | Android fork; GPL-2.0 repository designation. Site documents appearance controls, folder icons, sticker sizing, translation engines and voice transcription. | Useful, discoverable customization matters. External translation/transcription data flows require separate assessment. |
| [Forkgram F-Droid listing](https://f-droid.org/packages/org.forkgram.messenger/) and [source](https://github.com/Forkgram/TelegramAndroid) | Local pins, message navigation and metadata controls. Catalog identifies its nonfree network dependency; source describes a telemetry policy. | Small patches and transparent distribution are attractive. Verify our own build and network behavior before making privacy claims. |
| [Official Android source](https://github.com/DrKLO/Telegram) | Existing Android app, upstream history and build instructions; GPL source. | Preferred Android foundation for a direct upstream relationship. |
| [Official desktop source](https://github.com/telegramdesktop/tdesktop) | C++/Qt application; GPLv3 with OpenSSL exception. | Preferred Windows foundation; native build and packaging complexity remain substantial. |
| [Materialgram](https://github.com/kukuruzka165/materialgram) | Desktop fork documenting appearance and navigation changes. | Focused desktop customization is feasible; combining fork patch stacks adds maintenance. |
| [Unigram](https://github.com/UnigramDev/Unigram) | Windows-specific alternative with Store and direct packages. | Evaluate Windows integration and accessibility. Its build and relative performance have not been reproduced here. |
| [AlternativeTo list](https://alternativeto.net/lists/40876/telegram-third-party-clients/) | Discovery directory across platforms. | Inclusion/popularity does not establish quality, security or maintenance guarantees. |

## Foundation decision: our engineering assessment

| Option | Benefit | Cost / unknown | Decision |
| --- | --- | --- | --- |
| Python + TDLib | Working experiments, rapid iteration | We must implement and verify extensive media, calls, notifications and messaging UI | Keep as R&D prototype |
| Official Telegram Desktop fork | Mature client foundation, direct upstream | C++/Qt dependency build and Windows integration need proof | Preferred production candidate, conditional on build spike |
| Unigram fork | Windows-focused product | Architecture/contributor requirements and baseline build need deeper evaluation | Fallback if desktop candidate has material limitations |
| Official Android fork | Direct upstream and existing touch client foundation | Signing, identity, push variants, dependencies and merges | Selected Android starting point |
| Nekogram/Forkgram fork | More customization already present | Another patch stack and release cadence to maintain | Design references; assess individual changes before adoption |

Forking source does not prove feature parity, a working Felogram binary or
security. No evidence here establishes a universally best client. Evaluate
completed user journeys, reliability, accessibility and maintenance instead.

## Snapshots and build feasibility

GitHub API metadata inspected during research:

- Desktop candidate: `d8594c011756265de4385408540bd9f7c787a003` on `dev`.
- Android candidate: `f2908b14133bbffbf7ab04f641ecb5bfaf533242` on `master`.

These are research snapshots. Choose a tested upstream release baseline for
distribution; record actual checkout and recursive submodule SHAs per build.

The [Windows guide](https://github.com/telegramdesktop/tdesktop/blob/dev/docs/building-win.md)
currently specifies Visual Studio 2026, SDK 10.0.26100.0 and selected toolset
14.44, plus native dependency preparation. The
[Android guide](https://github.com/DrKLO/Telegram/blob/master/README.md) specifies
Android Studio 2025.1.4, NDK 27.2.12479018 and SDK 36. Recheck the pinned source's
instructions before installation. Builds have not been reproduced in this study.

## Implementation boundaries

[Telegram API terms](https://core.telegram.org/api/terms) require own credentials,
independent branding, expected messaging behavior and sponsored-message support;
they disallow ghost/read-status tampering. Focus tools should change local
organization and notification choices while preserving communication semantics.
AI features are deferred pending review of terms and specific data flows.

Original Python remains MIT. Native forks retain upstream licenses/notices;
copied GPL code must not be presented as MIT. Review exact license files,
submodules and bundled dependencies before distribution. API registration is
still an external dependency: client changes do not resolve my.telegram.org's
generic registration ERROR.

## Next experiments

1. Reproduce unmodified native builds, then independent app identities.
2. Compare upstream and Felogram on identical hardware, account data and network.
3. Test support groups, release channels, code/files, Android one-handed use and
   Windows keyboard-only use with actual users.
4. Verify background notifications, offline recovery, account isolation,
   accessibility, storage and update behavior; publish methods and failures.
5. Trial an upstream merge after the first feature. Simplify changes that cannot
   remain localized rather than growing an unmaintainable patch stack.
