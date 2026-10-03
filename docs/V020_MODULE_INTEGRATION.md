# v0.2.0 module integration

The ColorOS 17 native-first foundation is packaged into the same KernelSU/Magisk-style module as the clean-room Monet overlays.

## Install-time behavior

- Android < 17 / SDK < 37: native foundation is skipped.
- SDK 37 plus a ColorOS/OPlus 17 build marker: native foundation is mounted under `system/product/overlay`.
- Other Android 17 OEMs: skipped.
- Existing resource-only overlays remain independently configurable.

## Runtime behavior

The native foundation overlays are static system overlays. The service does not force-enable them; it only records PackageManager / OverlayManager state after boot.

This avoids treating immutable OEM-style RROs as user-switchable overlays.

## Safety

The installer does not restart SystemUI or apps. Activation occurs at the normal reboot boundary required by the systemless overlay mount.
