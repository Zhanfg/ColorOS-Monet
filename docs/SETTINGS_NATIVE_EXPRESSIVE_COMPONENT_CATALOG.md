# Settings native Expressive component catalog

Codex and the Android 17 upstream comparison show that a large part of the desired MD3E behavior already exists inside the current Settings/SettingsLib stack.

The correct implementation strategy is therefore **activation and integration**, not recreation.

## What is already native

When `SettingsThemeHelper.isExpressiveTheme(context)` is true, the Settings stack can switch to native Expressive behavior including:

- `SettingsPreferenceGroupAdapter` group-position state;
- native first/middle/last/single rounded-group geometry;
- Expressive switch surfaces/thumb;
- spinner and dropdown surfaces;
- search-box iconography;
- filled/outlined button backgrounds;
- header/zero-state/status-banner surfaces;
- toolbar/menu Expressive assets.

These resources are already present in the current ColorOS 17 Settings package and overlap the Android 17 Settings/SettingsLib upstream.

## What remains ColorOS-specific

The OPlus homepage still owns:

- `top_level_settings_oplus.xml`;
- OPlus preference subclasses;
- two-tone icon handling;
- tint categories;
- OEM feature rows.

Therefore enabling the native SettingsLib Expressive path must not imply replacing the OPlus homepage XML or its icon/tint owner.

## Consequence for v0.2.0

Do not recreate Settings MD3E with:

- package-wide CardHook;
- package-wide ListHook;
- global COUI radius/divider mutations;
- manually cloned SettingsLib backgrounds.

Instead:

1. validate the native Expressive gate on the live ColorOS build;
2. preserve OPlus homepage row/icon ownership;
3. use the native SettingsLib Expressive components where the framework selects them;
4. add only small component-scoped bridges for gaps.

Machine-readable policy:

`compat/coloros17/settings_expressive_component_catalog.tsv`
