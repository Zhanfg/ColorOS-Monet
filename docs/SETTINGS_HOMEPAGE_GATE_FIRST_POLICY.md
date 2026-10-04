# Settings homepage gate-first icon policy

The current ColorOS 17 OPlus homepage has two independent visual owners:

1. **group/row geometry** can inherit the native Android 17 SettingsLib
   Expressive adapter when the Settings Expressive gate is active;
2. **homepage glyph/tint treatment** remains owned by OPlus preference classes
   (`SettingJumpPreference`, `SettingSwitchPreference`, subclasses and
   `top_level_settings_oplus.xml`).

This means the 18 reviewed alternate glyphs are **not** the first implementation
step.

## Primary runtime policy

For all 42 icon-bearing OPlus homepage rows:

`KEEP_CURRENT_GLYPH + OPLUS_PREFERENCE_GLYPH_AND_TINT`

First test the native Settings Expressive gate by itself.

If the gate already produces a coherent homepage, no glyph bridge is required
for rows whose existing OPlus glyph remains semantically and optically correct.

## Secondary candidates

The existing reviewed alternatives are preserved only as a second-stage visual
experiment:

- 12 native Expressive glyph candidates;
- 6 Google Material Symbol candidates;
- 24 rows have no replacement candidate and remain OEM-native.

They may be tested only **after** the native gate A/B result is reviewed.

Machine-readable contract:

`compat/coloros17/settings_homepage_runtime_policy.tsv`

The experiment builder now refuses to build unless
`--after-native-gate` is passed explicitly.

## Why

The Android 17 native Settings Expressive gate can change SettingsLib
group/component behavior, while the 42 static ColorOS homepage glyphs remain
OPlus-owned unless proven otherwise. AOSP `DashboardFeatureProviderImpl`
does provide Expressive normalization for dynamic/injected Dashboard Tiles,
but that path is not evidence that the 42 static `top_level_settings_oplus.xml`
rows use it. Replacing glyphs before testing the native gate would combine two
independent changes and make regressions impossible to attribute.

Therefore the order is:

```text
OPlus current glyph/tint
        ↓
native Settings Expressive gate
        ↓
visual review
        ↓
only if a specific glyph is still weak:
native Expressive / Material Symbol secondary probe
```
