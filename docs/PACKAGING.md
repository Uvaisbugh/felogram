# Windows packaging verification

Run `powershell -File scripts/build_windows.ps1` from the project.
The bundle lives at `dist/Felogram/Felogram.exe`. Keep its `_internal` directory
beside the executable. This prototype uses a console for diagnostic output.

The script installs locked packaging dependencies, limits PATH to the Python
runtime and Windows directories, builds with PyInstaller, and runs `--probe`
and `--smoke-test`. The clean PATH prevents an unrelated application's DLL from
being accidentally bundled. A local build initially picked up Poppler's ICU DLL;
its exported symbols did not match Qt. Rebuilding with the restricted PATH fixed
the native loader and desktop smoke checks.

Local verification on 2026-10-05: Windows 11 build 26300, Python 3.14.7,
PyInstaller 6.22.3, TDLib 1.8.67. Both packaged probes passed.

The manually dispatched Windows package smoke workflow repeats the build on a
fresh GitHub Windows runner and executes it with external Python paths removed.
It deliberately does not upload a downloadable binary or attach an installer
to a release. Account login, delivery and session reopening still need manual
end-user checks. Binary redistribution remains gated on complete native notices,
including transitive components, as described in THIRD_PARTY_NOTICES.md.
