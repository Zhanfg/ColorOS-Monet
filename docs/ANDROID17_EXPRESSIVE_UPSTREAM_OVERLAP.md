# Android 17 Expressive upstream overlap

Exact Android 17.0.0 r1 sources are now pinned for both Settings and frameworks/base.

## Result

The current ColorOS 17 derived inventory contains **91 unique named Expressive resources** after generated-frame deduplication.

Exact name/path cross-check against Android 17.0.0 r1 finds:

- **88 / 91** in public AOSP Android 17 sources;
- Settings contributes the app-specific Expressive icons/layout assets;
- SettingsLib contributes the shared card/button/switch/spinner/toolbar/status-banner resources;
- SystemUI contributes the shared SystemUI Expressive glyphs;
- framework core contributes the three autofill/bottom-sheet Expressive resources.

Only these three remain outside the checked AOSP trees:

- `sud_ic_switch_check_mark_expressive`
- `sud_ic_switch_selector_expressive`
- `sud_ic_switch_uncheck_mark_expressive`

The `sud_` prefix strongly indicates the SetupDesign dependency family, so they are **not** treated as ColorOS-original artwork, but their exact upstream remains unresolved and they stay out of automatic replacement.

## Important architecture consequence

For Settings/SystemUI, most of the "new MD3E icons" we were considering are already Android 17 Expressive assets shipped inside the ColorOS build.

Therefore the preferred implementation path is not bulk icon replacement. It is:

1. verify the actual Expressive UI gate / consumer;
2. let the native component select its existing Expressive asset;
3. only use Material Symbols when the current component has no native/AOSP Expressive asset.

## Homepage behavior from AOSP Android 17

AOSP `TopLevelSettings.getPreferenceLayoutResId()` selects:

- `top_level_settings_expressive` when `SettingsThemeHelper.isExpressiveTheme(context)` is true;
- otherwise `top_level_settings`.

`SettingsHomepageActivity.onCreate()` also switches to `Theme_Settings_Home_Expressive` through the same gate.

Homepage icon resources such as `ic_homepage_display`, `ic_homepage_battery`, `ic_homepage_about` and `ic_homepage_security` are **layer-list components**:

- 40dp `AdaptiveIconShapeDrawable` colored background;
- 24dp Expressive foreground glyph;
- 8dp foreground inset.

This is why copying a 24dp glyph alone is not a faithful MD3E homepage migration.

## Files

- `compat/material-symbols/android17-expressive-upstream.lock`
- `compat/material-symbols/android17_expressive_overlap.tsv`
