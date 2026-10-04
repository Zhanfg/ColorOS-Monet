# Android 17 AOSP reference for Expressive / Monet

This project uses AOSP Android 17 only as a **public reference** for semantics and
component integration. ColorOS ownership is still verified independently from
the user's ROM snapshot.

## Release baseline

The Android platform manifest's `android-latest-release` branch was updated to
`android17-release`.

The Android 17 release manifest commit used as the public reference is:

`29ace668ae756c7b8917c57abb440f6518844b0c`

The manifest default revision is `android17-release`, and
`platform/packages/apps/Settings` follows that branch.

## AOSP theme-style parsing

Android 17 SystemUI's ThemeOverlayController reads:

`Settings.Secure.THEME_CUSTOMIZATION_OVERLAY_PACKAGES`

and parses:

`android.theme.customization.theme_style`

with `Style.valueOf(...)`.

The system-wide allow-list includes:

- EXPRESSIVE
- SPRITZ
- TONAL_SPOT
- FRUIT_SALAD
- RAINBOW
- VIBRANT

Content is intentionally not a system-wide theme style.

This establishes that the literal string `EXPRESSIVE` is a valid AOSP
system-wide Monet style identifier.

It does **not** prove that directly editing the secure JSON is a complete
ColorOS UXDesign apply operation.

## AOSP Expressive palette

The public AOSP ColorScheme implementation includes an EXPRESSIVE CoreSpec.

The high-level palette intent differs from TONAL_SPOT:

- primary hue is shifted substantially from the source seed;
- secondary/tertiary use dedicated expressive hue functions;
- neutral palettes receive their own small hue/chroma treatment.

For v0.2.0 this remains a reference only. The ColorOS hard-analysis report
already proves that native SystemUI uses its own current SPEC_2026 path, so the
module must not create a parallel AOSP/COE palette engine.

## Practical rule

AOSP proves **meaning and expected integration semantics**.

ColorOS ROM evidence decides:

- actual owner;
- active consumer;
- actual resource;
- classloader/plugin boundary;
- whether a hook/RRO is allowed.

Therefore:

```text
AOSP says EXPRESSIVE exists
        !=
module may force ColorOS to EXPRESSIVE at boot
```

The shipping module continues to consume the currently active ColorOS palette
and leaves theme ownership to the user/native UXDesign flow.
