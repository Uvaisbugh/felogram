# Native foundations: section-by-section progress

This records actual work on 2026-10-05. Stages stay open until their acceptance
evidence exists. No native Felogram release is implied by downloading source.

## Section 1: Android build foundation

Purpose: establish a reproducible official-source baseline before customization.

Completed:

- Full fork source checked out locally under `build/felogram-android`.
- All 15 direct submodules checked out to upstream's pinned revisions.
- Fixed the media submodule's Windows filename-length checkout failure using
  repository-local `core.longpaths` settings.
- Downloaded/invoked the upstream Gradle 8.13 wrapper on JDK 17.0.20.1.
- Added a PowerShell wrapper/helper and documented exact prerequisites in the
  [Android fork](https://github.com/Uvaisbugh/felogram-android).

Host inventory: SDK 36, build tools 36.0.0 and CMake 3.22.1 are present. Installed
NDK 28.2.13676358 initially differed from pinned requirement 27.2.12479018.
Preflight correctly reported it. Gradle installed the exact NDK using existing
accepted SDK licenses; preflight now passes. No Android device is connected.

Default baseline task: `:TMessagesProj_App:assembleAfatDebug`. Build result and
remaining blockers will be recorded after the attempt, separately from wrapper
and build-plugin compilation. Baseline uses upstream identity/configuration and
is not a Felogram-distribution candidate.

## Section 2: Windows native build foundation

Purpose: prove a mature C++/Qt baseline before migrating product work.

Completed: checked out official source snapshot
`d8594c011756265de4385408540bd9f7c787a003`, inspected its build guide, preparation
script and Qt version selection. Added a repeatable, read-only host preflight.

The host has Windows SDK 10.0.26100.0. The initial default vswhere query missed
Build Tools installations. A corrected query using `-products '*'` and the C++
component requirement found VS Build Tools 18.9.12120.119. Only MSVC 14.51.36231
is installed; initializing required toolset 14.44 failed. An attempt to add
Microsoft's 14.44 component exited 5007, requiring elevated installer execution.
Dependency preparation remains open. Do not label the Python executable a
native production build.

The source's Windows build guide specifies VS 2026 with selected toolset 14.44;
its AGENTS file also contains older VS 2022 setup references. Resolve the exact
compiler against this pinned guide/build scripts, not an assumed default toolset.
The x64 default chooses patched Qt 5.15.19; `qt6` selects Qt 6.11.2. Dependency
preparation can be extensive. Start with Debug and skip release dependency work
where supported. API configuration is another unresolved setup dependency.

```powershell
./scripts/check_native_windows.ps1
```

Exit 1 identifies missing prerequisites; exit 0 only confirms presence checks,
not a successful dependency/native build. No system configuration is changed.

## Section 3: independent identity

Next after baseline proof: package/storage names, app branding/icons and source
links; own API/push identities and private signing. Must install beside upstream
without replacing its sessions. No completed branding or signed APK claimed.

## Section 4: everyday-client verification

Two-account text/media/file tests, editing/retry/reconnect, session persistence,
notifications, account isolation and accessibility require running native apps
and real devices/accounts. These gates remain open.

## Section 5: Felogram workflows and releases

Implement local workspaces/bookmarks, exact code copy and reusable searches one
at a time after baseline verification. Measure against upstream, rehearse merges,
then verify signing, notices, install/update/uninstall. See
[product plan](PRODUCT_PLAN.md) and [foundation decision](adr/002-production-platform-foundations.md).
