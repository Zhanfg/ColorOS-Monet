# Runtime evidence collector after Codex analysis

The static Codex reports are complete. Their remaining release gates are mostly
runtime provenance/binding questions, so the next device-side collector is kept
small and read-only rather than extracting more APKs.

Script:

`scripts/ColorOS17_MD3E_RuntimeEvidence_v1.sh`

## What it collects

- device/build/theme JSON and native Expressive gate state;
- exact package code paths, versions and APK SHA-256 values;
- running Settings/SystemUI/UXDesign process mappings;
- focused activity/window ownership signals;
- relevant SurfaceFlinger layer names;
- OverlayManager/idmap/resource-lookup state;
- filename/size/mtime/SHA-256 fingerprint of `/data/oplus/uxres/uxcolor`
  without copying the XML contents;
- narrowly filtered COE/card/QS/media/volume error and class logs.

## What it deliberately does not collect

- screenshots;
- UIAutomator text hierarchy;
- arbitrary app logs;
- app-private user data;
- raw UXDesign color XML payloads;
- system APKs or DEX files already captured previously.

## Safety

No reboot, force-stop, overlay enable/disable, theme mutation or SystemUI
restart is performed.

This closes as many Codex runtime gates as shell-level evidence can. Any
remaining active-instance question is then a candidate for a tiny diagnostic
LSPosed trace rather than another broad ROM dump.
