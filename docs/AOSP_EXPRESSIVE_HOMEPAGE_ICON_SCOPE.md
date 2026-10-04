# Android 17 homepage icon normalization vs ColorOS static homepage rows

Pinned AOSP Settings commit:

`213829fb67f5e070029e0513a088f31bc8f5c1ed`

contains a native Expressive icon path in
`DashboardFeatureProviderImpl.setPreferenceIcon(...)`.

## What AOSP actually proves

For a **Dashboard Tile** in `CATEGORY_HOMEPAGE`:

```text
Tile icon
  -> setPreferenceIcon(...)
  -> SettingsThemeHelper.isExpressiveTheme(...)
  -> getExpressiveHomepageIcon(...)
  -> normalize inner drawable to dashboard_tile_image_size
  -> choose tile ColorScheme foreground/background
  -> AdaptiveIcon(foreground + rounded/background container)
```

The original inner glyph is therefore preserved while the Expressive path owns
normalization, tint and background/container treatment.

This is strong evidence for the Android 17 dynamic/injected homepage-tile
contract.

## What it does NOT prove

The current ColorOS homepage's 42 primary rows come from:

`top_level_settings_oplus.xml`

and are bound by OPlus preference subclasses whose icon/two-tone fields are
already proven.

There is no static evidence that those 42 XML-defined rows pass through
`DashboardFeatureProviderImpl.setPreferenceIcon(...)`.

Therefore we must not claim that enabling the Settings Expressive gate will
automatically wrap or recolor every static OPlus homepage glyph using the AOSP
Dashboard Tile path.

## Correct owner split

For the current ColorOS build:

- **group/list geometry and SettingsLib component selection**
  -> native Settings Expressive gate may affect these; verify with A/B probe.
- **42 static OPlus homepage glyphs/two-tone categories**
  -> OPlus preference classes remain the proven owner.
- **dynamically injected Dashboard Tiles**
  -> AOSP `DashboardFeatureProviderImpl` Expressive icon normalization is a
  valid reference and may remain active.
- **row-specific glyph replacement**
  -> second-stage experiment only after native-gate visual review.

This distinction keeps the project from attributing a dynamic Tile code path to
static vendor XML rows.
