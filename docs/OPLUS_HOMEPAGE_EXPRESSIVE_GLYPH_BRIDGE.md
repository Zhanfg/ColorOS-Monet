# OPlus homepage Expressive glyph bridge policy

The current ColorOS Settings homepage has **two separate icon systems** in the same APK:

1. the visible OPlus homepage rows from `top_level_settings_oplus.xml`, whose preference classes own `showTwoToneColor`, `tintType`, `needChangeDrawType` and related state;
2. Android 17/AOSP-style `*_expressive` drawables, most of which are `TintDrawable` wrappers over filled base glyphs.

These ownership layers must not be stacked blindly.

## Verified wrapper structure

Current Settings binary XML proves 24 Expressive foreground wrappers. Typical example:

```text
ic_settings_battery_expressive
    -> TintDrawable
    -> tint = homepage_battery_foreground
    -> drawable = ic_settings_battery_filled
```

The full derived table is:

`compat/material-symbols/coloros17_settings_expressive_wrappers.tsv`

## Bridge rule

When experimentally replacing an OPlus homepage glyph with a native Expressive candidate, the default source is the **wrapped base glyph**, not the `TintDrawable` wrapper.

Why:

- glyph geometry comes from the wrapped filled/native drawable;
- OPlus preference classes remain the proven tint/two-tone owner;
- importing the whole TintDrawable wrapper would introduce a second foreground tint owner and can defeat `tintType` category behavior.

Therefore:

```text
OPlus row/container/two-tone owner
    -> replacement glyph geometry only
    -> OPlus runtime tint remains authoritative
```

The experiment builder supports `--native-wrapper` only for controlled comparison. It is not the default and is not shipping-enabled.

## Release status

This remains an experiment. A candidate is not promoted merely because:

- the native Expressive wrapper exists;
- its base glyph exists;
- the RRO compiles.

Promotion still requires the native Settings gate A/B review and actual OPlus row rendering verification.
