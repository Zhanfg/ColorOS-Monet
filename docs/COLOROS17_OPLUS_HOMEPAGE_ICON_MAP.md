# ColorOS 17 OPlus homepage icon source map

The archived ColorOS 17 Settings APK was decoded directly with Android 17 `aapt2`.

Package:

- `com.android.settings`
- version: `17.0.0`
- target SDK: 37
- APK SHA-256: `e285088674907eedef89b4ba9862165dd070699cba4303c4b05b969f99c4261d`

## Exact OPlus homepage XML

`res/xml/top_level_settings_oplus.xml` is present and contains the actual ColorOS homepage preference classes, keys, current icon resources, controllers and OPlus tint metadata.

Important: ColorOS does **not** simply use the AOSP `top_level_settings_expressive.xml` homepage. Its visible homepage remains OPlus-owned.

Examples:

- `wifi_settings` → `SettingsSimpleJumpPreference` → `settings_wifi_ic`
- `bluetooth_settings` → `SettingsSimpleJumpPreference` → `settings_bluetooh_ic`
- `display_and_brightness` → `settings_brightness_ic`
- `about_phone` → `settings_about_device_ic`

Most OPlus entries already expose:

- `showTwoToneColor=true`
- a ColorOS `tintType`
- in many cases `needChangeDrawType=true`

Therefore the OPlus preference class remains the owner of the outer icon treatment.

## Expressive resources in the same APK

The same Settings APK contains the complete Android 17 Expressive wrapper family, including:

- `ic_settings_about_device_expressive`
- `ic_settings_battery_expressive`
- `ic_settings_display_expressive`
- `ic_settings_location_expressive`
- `ic_settings_privacy_expressive`
- `ic_settings_safety_center_expressive`
- `ic_settings_system_dashboard_expressive`
- `ic_settings_wallpaper_expressive`
- `ic_volume_up_expressive`
- `ic_apps_expressive`
- `ic_notifications_expressive`
- `ic_help_expressive`

Decoded AOSP-style homepage layer lists in the ColorOS APK reference these wrappers directly. For example:

`ic_homepage_about -> ic_settings_about_device_expressive`

`ic_homepage_battery -> ic_settings_battery_expressive`

`ic_homepage_display -> ic_settings_display_expressive`

`ic_homepage_sound -> ic_volume_up_expressive`

This proves that ColorOS ships both the OPlus homepage presentation and the Android 17 Expressive drawable family.

## Mapping policy

The machine-readable map is:

`compat/coloros17/settings_oplus_homepage_icons.tsv`

Each visible OPlus homepage entry receives one of:

- `NATIVE_EXPRESSIVE`
- `MATERIAL_SYMBOL_CANDIDATE`
- `KEEP_NATIVE`
- `NEEDS_REVIEW`

The current map deliberately keeps OPlus/device-specific features native.

Material Symbols is used only for generic gaps such as airplane mode, Wi-Fi, Bluetooth, lock and legal information.

## Shipping implication

Do not globally replace OPlus homepage icons.

The safe future implementation is component-aware:

1. keep the OPlus preference class/container/two-tone treatment;
2. replace only the inner glyph source where the semantic mapping is exact;
3. prefer a native ColorOS/AOSP Expressive wrapper already in the APK;
4. fall back to the pinned Google Material Symbol only where no native Expressive equivalent exists;
5. leave OEM-specific features unchanged.

Activation remains experimental until the on-device native Expressive probe confirms the final OPlus rendering path.
