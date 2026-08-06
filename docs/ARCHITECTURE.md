# Architecture

## Build layer

Each target is an independent code-free RRO APK. Application mappings are stored as TSV metadata and converted into `values/colors.xml` plus `values-night/colors.xml` during the Gradle build.

The generated values reference Android's public dynamic palette resources (`system_accent*` and `system_neutral*`). No wallpaper color is baked into an APK.

## Module layer

The module base is target-agnostic:

1. `customize.sh` reads persistent feature flags and copies only requested overlays.
2. `service.sh` waits for Android boot completion, applies dynamic overlay state through `cmd overlay`, and writes diagnostics.
3. `action.sh` updates feature flags with volume-key input.
4. `uninstall.sh` removes persistent project state.

## Compatibility limits

RRO enforcement varies by Android version, target `overlayable` declarations, signing policy, and OEM idmap configuration. A successfully compiled APK is not proof that the target permits every resource override. Device logs are authoritative.
