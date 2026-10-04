# Android 17 Settings upstream pinning policy

ColorOS-Monet uses two AOSP Settings references for different purposes.

## Reproducible baseline

Pinned release:

- tag: `android-17.0.0_r1`
- Settings commit: `213829fb67f5e070029e0513a088f31bc8f5c1ed`

This is the immutable reference used when documenting Android 17 Expressive
wrappers and behavior.

## Moving maintenance branch

The project also monitors:

`refs/heads/android17-release`

for later Expressive resource changes.

Branch-only changes are **not** automatically promoted into ColorOS mappings.
They are drift signals. A new resource is eligible only when the current
ColorOS target also contains or demonstrably consumes the corresponding
component.

This separates reproducibility from update awareness.
