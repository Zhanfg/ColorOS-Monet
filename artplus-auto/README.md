# ColorOS 17 ART+ Auto Compiler

Experimental on-device compiler for ColorOS 17 ART+ icon assets.

## Current alpha scope

- Scans user-installed apps that expose a launcher activity.
- Adaptive icons: reads the native background / foreground / monochrome layers directly.
- Legacy icons: estimates a spatial background in OKLab, derives a soft foreground alpha, restores anti-aliased foreground colors by inverse compositing, and falls back conservatively when confidence is low.
- Dark mode: generates `rec_night` from the foreground only. It does not flatten the foreground and background together.
- Monochrome: preserves an APK-provided monochrome layer when available, otherwise derives a subject mask; opaque legacy tiles use an AOSP-style luminance fallback.
- Writes native ART+ files to `/data/oplus/uxicons/<package>` through root.
- Produces the ColorOS span variants `1x2`, `2x1`, and `2x2`.
- Refreshes ColorOS icon configuration by updating `mUxIconConfig`, broadcasting `oplus.intent.action.SKIN_CHANGED`, and returning to HOME.
- Caches by package version + icon resource + generator version.

## ColorOS 17 loader findings used by this implementation

The ColorOS 17 launcher examined for this branch resolves ART+ foreground state roughly as:

- dark redraw -> `rec_night`
- monochrome/themed -> `monochrome`
- normal -> `recfg`
- background -> `recbg` (with theme-specific alternatives such as `daybg`)

The system loader includes `/data/oplus/uxicons/` as a native search root. This is why the alpha writes there directly instead of rebuilding the old static `/my_product/media/theme` overlay.

## Safety boundary

The default alpha intentionally does not rewrite system applications. Low-confidence legacy separation falls back to retaining the complete source icon rather than destructively removing pixels.

## Build

The GitHub Actions workflow `artplus-auto.yml` builds and lints the debug APK and publishes it as an artifact.

Local requirements: JDK 17+, Android SDK 35, Gradle 8.9+.

```bash
gradle -p artplus-auto :app:lintDebug :app:assembleDebug
```

This code is project-authored and follows the parent repository Apache-2.0 license.
