# Research and setup plan

Assessment date: 2026-09-28. Target: Windows 11, x64.

## Decision

Use the installed CPython 3.14.7 with PySide6 6.11.2, the `tdjson` 1.8.67 Python
binding, and one dedicated TDLib worker. Keep application logic independent of Qt
and the native binding. Use uv, Ruff, mypy, and pytest.

The foundation was subsequently implemented and verified on this machine.
Dependency installation, native TDLib loading, window startup, queued event
delivery, and graceful shutdown pass. Packaging remains a later milestone.

## What the current ecosystem supports

| Component | Evidence checked | Consequence |
| --- | --- | --- |
| TDLib | Official source declares 1.8.67; the JSON API is documented and has an official Python example. | Keep TDLib responsible for Telegram networking, synchronization, and its local database. |
| PySide6 | PyPI lists 6.11.2, Python `>=3.10,<3.15`, and a Windows x64 stable-ABI wheel. | Installed Python 3.14.7 is a suitable initial interpreter. |
| `tdjson` | PyPI lists 1.8.67 and `tdjson-1.8.67-cp314-cp314-win_amd64.whl`; the project bundles TDLib. | Start with this binary package instead of requiring a local C++ build. It is a third-party binding, not an official Telegram Python package. |
| QtAsyncio | Qt still labels it a technical preview and documents only the fundamental asyncio layer as covered. | Avoid making it a foundation dependency. |
| qasync | Its current README declares Python `>=3.8,<3.14`. | It is not the documented match for the installed interpreter. |
| PyInstaller | Current requirements support Python 3.14; PyPI lists 6.22.3. | Use a Windows one-folder build for the first packaging experiment. |

Sources: [TDLib source version](https://github.com/tdlib/td/blob/master/CMakeLists.txt),
[TDLib overview](https://github.com/tdlib/td),
[PySide6 release](https://pypi.org/project/PySide6/6.11.2/),
[`tdjson` release files](https://pypi.org/project/tdjson/1.8.67/#files),
[QtAsyncio](https://doc.qt.io/qtforpython-6/PySide6/QtAsyncio/index.html),
[qasync requirements](https://github.com/CabbageDevelopment/qasync#requirements),
[PyInstaller requirements](https://pyinstaller.org/en/stable/requirements.html).

### Python-to-TDLib options

| Option | Assessment |
| --- | --- |
| `tdjson` | Recommended: a small native wrapper around the four modern JSON entry points, with a matching Windows wheel. Its receive implementation releases the Python GIL while waiting. We still own request tracking, lifecycle, validation, and domain conversion. |
| Direct `ctypes` over `tdjson.dll` | Supported by Telegram's Python example and a viable fallback. Adds responsibility for DLL discovery, function signatures, dependent DLLs, and the native build. Implement only if the packaged binding becomes unsuitable. |
| `python-telegram` | Its README explicitly excludes Windows. Do not choose it for this Windows-first project. |
| `aiotdlib` | Its README targets TDLib 1.8.46, warns about pre-1.0 changes, and lists bundled binaries for macOS ARM64 and Debian AMD64. More adaptation is needed for this environment. |
| Custom C++ binding | Adds work already covered by `tdjson` without a current product requirement. |

This comparison does not establish that every other binding is abandoned.
It selects the smallest documented fit for the present platform.

Sources: [`tdjson` project](https://github.com/AYMENJD/tdjson),
[`tdjson` native boundary](https://github.com/AYMENJD/tdjson/blob/main/tdjson/tdjson.cpp),
[official ctypes example](https://github.com/tdlib/td/blob/master/example/python/tdjson_example.py),
[`python-telegram`](https://github.com/alexander-akhmetov/python-telegram),
[`aiotdlib`](https://github.com/pylakey/aiotdlib).

## Architecture and concurrency

```text
PySide6 window and presentation controller              [main thread]
    |
    | application commands / immutable result events
    v
Application services and small domain types             [no Qt imports]
    |
    v
TDLib runtime: command queue, request tracking, lifecycle [one worker]
    |
    v
Tdjson adapter -> tdjson extension -> TDLib
```

Use Qt Widgets for the initial window. Choose between a model/view Widgets chat
UI and Qt Quick/QML when the first conversation view is designed; the transport
and application layers should not depend on that choice.

The runtime's receive loop is ordinary Python code hosted by a QThread in the
desktop application. Commands enter through a thread-safe queue. A Qt bridge
delivers results to the presentation controller through queued signals. A future
CLI can host the same runtime without importing Qt.

Design rules for the implementation:

1. One process-wide owner calls `td_receive`, including when multiple accounts
   are eventually supported. Route results using `@client_id`; correlate replies
   using a unique `@extra`. Apply updates in receive order.
2. Keep all native calls in this worker initially, including the limited
   synchronous calls supported by `td_execute`. Use short, bounded receive waits
   so the loop can service commands, timeouts, and shutdown requests.
3. A QThread running a blocking loop cannot rely on queued slots in that same
   worker to process stop commands. The command queue carries stop requests.
   Connect result signals to QObject slots owned by the main thread.
4. Update widgets and Qt models only on the main thread. Avoid a signal per field
   or unbounded UI event growth; batch presentation updates and define overload
   behavior before handling large histories. Never silently discard authoritative
   TDLib updates.
5. On exit, stop accepting work, send `close`, continue receiving until each
   client reaches `authorizationStateClosed`, then finish the worker. Keep the UI
   responsive during this sequence and report shutdown timeouts.
6. Expose only the operations the current milestone needs. Add ChatService and
   MessageService when their features arrive. Do not generate empty service,
   plugin, or alternative-protocol layers.

The first two points follow TDLib's documented interface contract; the queue,
thread host, and presentation boundary are project design choices.
[TDLib JSON API](https://core.telegram.org/tdlib/docs/td__json__client_8h.html),
[Qt thread ownership and signals](https://doc.qt.io/qt-6/qthread.html).

TDLib owns Telegram persistence. Initially, application settings can be small
configuration values. Introduce separate SQLite storage only when bookmarks,
workspaces, or other application-owned records justify it. Do not modify TDLib's
database or duplicate its network synchronization engine.

## Local environment checked

| Tool | Observed on this machine |
| --- | --- |
| OS / architecture | Windows 11, build 26200; x64 |
| CPython | 3.14.7, 64-bit, `C:\Python314\python.exe` |
| uv | 0.12.10 |
| Git | 2.55.0.windows.5 |
| Visual Studio Build Tools | 2026, 18.9.2; C++ x64/x86 component detected |
| MSVC toolset directory | 14.51.36231 |
| Windows SDK include directory | 10.0.26100.0 |
| Bundled CMake | 4.3.1-msvc1 |
| Bundled Ninja | 1.13.2 |
| PySide6 / tdjson | 6.11.2 / 1.8.67 installed in the project environment |

`cl`, CMake, and Ninja are not on the normal shell PATH, but were located inside
Visual Studio Build Tools. This is not evidence that they need reinstalling.
No native compilation was attempted. OpenSSL, zlib development libraries, and
gperf have not been established as available for a TDLib source build.

### If a source build becomes necessary

The official TDLib build requires a C++17 compiler, CMake 3.10+, OpenSSL, zlib,
and gperf. Use the [official build generator](https://tdlib.github.io/td/build.html)
for Windows/Python and the selected compiler. The local compiler and CMake are
present, but dependency paths and runtime compatibility still need verification.

Pin the TDLib source commit and native dependency versions, configure an
out-of-source Release x64 build, and build the `tdjson` target. Keep the DLL and
its dependency DLLs in a project-specific runtime directory, loaded by explicit
path. Record the source revision and runtime version. Do not install arbitrary
DLLs into Windows system directories. The packaged binding path does not require
this build stage.

## Exact next setup sequence

These are the next implementation steps, not commands already executed.

1. Initialize Git in this directory and add ignore rules for environments,
   credentials, runtime state, logs, native builds, and application packages.
2. Add `pyproject.toml` with a packaged `src/felogram` layout and a `felogram`
   entry point. Use `requires-python = ">=3.14,<3.15"` for the tested baseline;
   record `3.14.7` in `.python-version`.
3. Create `.venv` with the existing interpreter using
   `uv venv --python C:\Python314\python.exe`.
4. Add runtime dependencies `PySide6==6.11.2` and `tdjson==1.8.67` with uv.
   Generate and retain `uv.lock`, including artifact hashes. Native packages must
   resolve to compatible wheels; investigate a missing wheel before building.
5. Add the checked development versions: `pytest==9.1.1`, `pytest-qt==4.5.0`,
   `ruff==0.16.9`, and `mypy==2.3.1`. Ruff handles formatting and linting;
   mypy checks typed application code; pytest-qt checks Qt event behavior.
6. Implement a minimal window, validated configuration, simple logging, and the
   transport boundary. Start with an application status service; no empty future
   services. Offer a useful error if the native runtime cannot load.
7. Implement the unauthenticated native probe described below. Run it outside the
   GUI first, then through the worker and presentation bridge.
8. Verify formatting, linting, types, isolated tests, native load, event delivery,
   UI responsiveness, and shutdown. Add Windows CI with `uv sync --locked` and
   those checks. Keep account-dependent tests outside the ordinary suite.
9. Make an early Windows one-folder packaging experiment with
   `PyInstaller==6.22.3` in a separate dependency group. Verify bundled Qt plugins
   and TDLib libraries; subsequently test on a clean Windows environment.
10. Record actual results and unresolved problems. The following milestone is
    explicit login with user-provided Telegram application credentials.

uv's [project structure documentation](https://docs.astral.sh/uv/concepts/projects/layout/)
describes the environment and lockfile model. The package versions above were
read from PyPI metadata on the assessment date and remain subject to the first
installation and smoke test.

### First milestone acceptance criteria

- Launch a minimal window titled Felogram with clear runtime status.
- Import the native binding and run `getTextEntities` on a synthetic string.
- Create a TDLib client and send `getOption` for `version`, with `@extra`.
- Receive the version response and the initial authorization-state update;
  show that the runtime is waiting for configuration.
- Send `close`, receive `authorizationStateClosed`, and finish without a live
  worker or hanging process. No API credentials are needed for these checks.
- Keep a UI timer responsive while the worker waits for native events.
- Test response correlation, missing libraries, malformed responses, timeouts,
  and shutdown with a fake transport; label the real native smoke test separately.
- Log operation names, state transitions, timings, and error categories. Avoid
  logging whole TDLib objects or private payloads by default.

This verifies Python-to-TDLib loading and event delivery. It does **not** prove an
authenticated connection to Telegram's servers. That requires configuration and
the later authentication milestone.

### Proposed first source files

```text
src/felogram/
  __init__.py
  main.py                 application composition and entry point
  config.py               validated settings
  logging_config.py       application logging
  application/
    runtime_status.py     status operations and presentation-neutral values
  telegram/
    transport.py          narrow transport contract and JSON boundary types
    tdjson_adapter.py     the only module that imports the native binding
    runtime.py            ordered receive loop, requests, close lifecycle
  ui/
    main_window.py        minimal window
    runtime_bridge.py     QThread host and queued signals
tests/
  test_config.py
  test_runtime.py
  test_window.py
  test_tdjson_smoke.py
```

Create files as their behavior is implemented. No plugin SDK, CLI framework,
separate database, media subsystem, or generated full TDLib model layer is needed
for this milestone.

## Subsequent milestones and limits

1. Authentication: configure TDLib, handle its actual authorization states,
   persist a session, and distinguish closing the app from logging out.
2. Messaging: chat list, paginated history, text send/receive, and update ordering.
3. Reliability: reconnect behavior, unread counts, message edits/deletions,
   recoverable failures, and repeatable packaging.
4. Productivity: keyboard navigation, search, tabs, and workspace organization.
5. Media and extensions: add queues, integrations, and user-controlled automation
   as separate features with clear boundaries.

Obtain `api_id` and `api_hash` through the official
[Telegram developer process](https://core.telegram.org/api/obtaining_api_id).
The first probe needs neither. Before persistent login, choose account-specific
data directories and protect the database encryption key with an OS credential
store. Do not treat an empty/default key as meaningful encryption at rest.

The pasted feature list describes ambitions, not unrestricted platform
capabilities. Telegram's current API terms restrict the use of Telegram data for
AI, including deployment; local inference is not automatically an exception.
Keep AI summaries and semantic indexing out of committed scope until the specific
use is assessed against those terms and the linked content terms.
[API terms, section 1.5](https://core.telegram.org/api/terms),
[content licensing terms](https://telegram.org/tos/content-licensing).

Main engineering risks are correct shutdown and request tracking, native wheel
and API-version changes, large-list rendering, and distribution of native
libraries. A matching wheel is evidence of installability, not proof of runtime
correctness. Pin and verify the runtime version and its schema assumptions.

Windows is the first tested target. The selected binding documents Linux x64/ARM64
and macOS ARM64 support; macOS Intel and Windows ARM64 need a separate decision.
PyInstaller builds must be produced on each target OS. Cross-platform support
remains unverified until those builds and smoke tests exist.
