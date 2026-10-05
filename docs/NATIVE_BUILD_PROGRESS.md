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

The ARM64 debug build completed successfully: 301 tasks, Gradle exit 0.
The Java/native application source remains upstream-derived; the build helper
selects ARM64. The preserved baseline APK is 63,947,343 bytes, SHA-256
`B14EB07113D1289A39E741048944CBCA91A7DD8FBEFCC64EE34C43ADAE130107`.
AGP emitted it under `TMessagesProj_App/build/intermediates/apk/afat/debug/app.apk`.
Signature verification passed (v1/v2). Identity is `org.telegram.messenger.beta`,
version 12.10.6, label Telegram Beta. This is not a Felogram release.

Offline startup passed in a fresh, isolated workspace AVD: API 37.2, x86_64 with
ARM64 translation, 16 KB pages, airplane mode enabled. Installation required
`adb install -t --abi arm64-v8a`; the debug build is test-only. Launch returned
Status ok and the welcome screen rendered; no fatal AndroidRuntime exception
was recorded. No sign-in or messaging was tested. The emulator was then closed
to free memory for Windows compilation. This does not replace ARM64-device tests.

Packaging limitation discovered: the injected ABI property limits compilation,
but the APK still contains other-ABI MLKit libraries without matching Telegram
libraries. A build-helper correction now filters packaged ABIs too; its rebuild
and artifact verification remain pending. Other ABI builds remain unverified.

## Section 2: Windows native build foundation

Purpose: prove a mature C++/Qt baseline before migrating product work.

Completed: checked out official source snapshot
`d8594c011756265de4385408540bd9f7c787a003`, inspected its build guide, preparation
script and Qt version selection. Added a repeatable, read-only host preflight.

The host has Windows SDK 10.0.26100.0. The initial default vswhere query missed
Build Tools installations. A corrected query using `-products '*'` and the C++
component requirement found VS Build Tools 18.9.12120.119. Initially only MSVC 14.51.36231
was installed; initializing required toolset 14.44 failed. An attempt to add
Microsoft's 14.44 component exited 5007, requiring elevated installer execution.
After administrator approval, the install succeeded (exit 0). MSVC 14.44.35207
is present and compiler preflight passes. Recursive upstream source checkout is
complete and Qt 6 Debug dependency preparation has started. Do not label the
Python executable a native production build.

The source's Windows build guide specifies VS 2026 with selected toolset 14.44;
its AGENTS file also contains older VS 2022 setup references. Resolve the exact
compiler against this pinned guide/build scripts, not an assumed default toolset.
The x64 default chooses patched Qt 5.15.19; `qt6` selects Qt 6.11.2. Dependency
preparation can be extensive. Start with Debug and skip release dependency work
where supported. API configuration is another unresolved setup dependency.

```powershell
./scripts/check_native_windows.ps1
./scripts/prepare_native_windows.ps1 -PreflightOnly
./scripts/prepare_native_windows.ps1
```

Exit 1 identifies missing prerequisites; exit 0 only confirms presence checks,
not a successful dependency/native build. The preflight changes no system settings.

The preparation helper builds Qt 6 Debug dependencies inside this project's build
directory, restores temporary environment settings and prevents overlapping
helper runs. The first attempt failed to load Windows PowerShell's archive module.
Using that shell's own module path fixed the failure without changing upstream
source. The retry completed dependency stages through libvpx (20/32). It was paused deliberately while Android finished to avoid exhausting this 16 GB host. Windows preparation resumed with those caches and passed Little CMS. The helper uses upstream's `silent` option to rebuild stale/partial caches without an interactive keypress, with unbuffered Python logging. FFmpeg preparation is underway; no native desktop executable exists yet.


On a fresh project checkout, prepare the pinned source first:

```powershell
git clone --depth 1 --filter=blob:none --branch dev https://github.com/telegramdesktop/tdesktop.git build/tdesktop-baseline
git -C build/tdesktop-baseline fetch --depth 1 origin d8594c011756265de4385408540bd9f7c787a003
git -C build/tdesktop-baseline checkout --detach d8594c011756265de4385408540bd9f7c787a003
git -C build/tdesktop-baseline config core.longpaths true
git -C build/tdesktop-baseline -c core.longpaths=true submodule update --init --recursive --depth 1
```

Keep completed dependency caches between attempts. The helper does not install
Visual Studio components or configure Telegram API credentials automatically.

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
