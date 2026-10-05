# Runtime dependency notices

Felogram's MIT license applies to original project source, not dependency code.
Installed metadata was inspected on 2026-10-05:

| Dependency | Pinned version | License reported by package metadata |
| --- | --- | --- |
| PySide6 | 6.11.2 | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only |
| tdjson | 1.8.67 | MIT |
| pywin32 | 312 | PSF |

TDLib and Qt are native components supplied by these packages. Binary release
preparation must inventory transitive native components and include their actual
license texts and required notices. This table is not a complete binary-distribution
license bundle. No desktop executable is being published with this source alpha.
