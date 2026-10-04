# Android 17 Settings native Expressive gate

The public Android 17.0.0 r1 implementation gives us an exact upstream contract for the Settings Expressive UI gate.

## SettingsThemeHelper

Source:

`frameworks/base/packages/SettingsLib/SettingsTheme/src/com/android/settingslib/widget/SettingsThemeHelper.kt`

Pinned frameworks/base commit:

`94b4c163b7dfe5ce3607f7bb8456f9573f7de57d`

For Android 17, `SettingsThemeHelper.isExpressiveTheme(context)` evaluates in this order:

1. SDK gate;
2. system property `is_expressive_design_enabled`;
3. optional Activity `ExpressiveDesignEnabledProvider`;
4. exported aconfig flag `Flags.isExpressiveDesignEnabled()`.

The flag declaration is:

- package: `com.android.settingslib.widget.theme.flags`
- container: `system`
- namespace: `android_settings`
- flag: `is_expressive_design_enabled`
- exported: true.

## AOSP Settings consumer

At Android 17.0.0 r1, `TopLevelSettings.getPreferenceLayoutResId()` selects:

- `top_level_settings_expressive` when `SettingsThemeHelper.isExpressiveTheme(context)` is true;
- `top_level_settings` otherwise.

`SettingsHomepageActivity.onCreate()` uses the same gate to select `Theme_Settings_Home_Expressive`.

This is a much stronger integration point than replacing the homepage icons one by one.

## Homepage icon composition

The AOSP homepage icon drawables are not bare glyph replacements.

For example `ic_homepage_display`, `ic_homepage_battery`, `ic_homepage_about` and `ic_homepage_security` are layer lists composed from:

- a 40dp `AdaptiveIconShapeDrawable` background;
- a 24dp Expressive foreground drawable;
- 8dp inset.

The current ColorOS 17 Settings package already contains the same Expressive foreground resource family.

## Project consequence

Before adding any custom Settings card or icon hook, determine the device's **actual native gate state**.

The runtime evidence collector now reads:

- `getprop is_expressive_design_enabled`;
- `device_config get android_settings is_expressive_design_enabled` when available;
- the current Settings/COUI runtime state.

If the ColorOS build preserves the native gate and consumer path, the preferred implementation is to use that native mechanism rather than synthesize a parallel Settings UI.

Do not mutate this gate in the shipping module until runtime behavior is verified. A hot test, if needed, belongs under `experiments/` and must be reversible without reboot.
