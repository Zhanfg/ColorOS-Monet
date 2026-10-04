# Settings native Expressive gate — static findings

The current ColorOS 17 Settings DEX contains a native layout-selection gate. This is more important than importing replacement icons blindly.

## Exact static flow

`TopLevelSettings.getPreferenceScreenResId()` calls:

`getContext() -> TopLevelSettings.getPreferenceLayoutResId(Context)`

The latter selects **three different preference-screen resource IDs**:

1. if `DesktopSettingsUtils.shouldShowTopLevelDeviceCategory(context)` is true:
   - `0x7f180267`

2. otherwise, if `SettingsThemeHelper.isExpressiveTheme(context)` is true:
   - `0x7f180266`

3. otherwise:
   - `0x7f180265`

This is directly observed from the current Settings `classes.dex`.

Separately, `OplusTopLevelSettings.getPreferenceScreenResId()` returns:

- `0x7f180269`

unconditionally in the analyzed method.

## Expressive gate is not the Monet variant

`SettingsThemeHelper.isExpressiveTheme(Context)` calls/uses:

- `SettingsThemeHelper.getPropBoolean(...)`
- `SettingsThemeHelper.getActivityFromContext(...)`
- `ExpressiveDesignEnabledProvider.isExpressiveDesignEnabled()`
- `SettingsThemeHelper.isExpressiveDesignEnabled()`

This reinforces the Codex finding that:

**Settings Expressive UI gating is not equivalent to choosing the UXDesign/Monet `EXPRESSIVE` palette variant.**

## Resource evidence already present

The current Settings APK contains, among others:

- `res/xml/top_level_settings_expressive.xml`
- `res/xml/top_level_settings_oplus.xml`
- `res/layout-v36/settingslib_expressive_preference.xml`
- `res/layout/settingslib_expressive_preference_card.xml`
- `res/layout-v36/settingslib_expressive_preference_category.xml`
- `res/layout-v36/settingslib_expressive_preference_switch.xml`
- the native `ic_settings_*_expressive` family.

The exact mapping from the four runtime IDs above to XML names still needs the binary resource-table/XML evidence requested by Codex. It is intentionally not guessed here.

## Architectural consequence

For Settings homepage/category icon work the order is now:

1. determine which native preference XML is actually selected;
2. determine whether the native Expressive gate is active/eligible;
3. prefer the ROM's already-wired Expressive icons/layouts;
4. use AOSP Android 17 as the integration reference;
5. use Google Material Symbols only for genuine glyph gaps.

Therefore the project must **not** generate a Settings-home icon-replacement RRO before the native gate/resource mapping is resolved.

## Evidence request

`scripts/ColorOS17_MD3E_NarrowEvidence_v2.sh` collects the exact relevant Settings XML plus framework bytecode without changing the UI.
