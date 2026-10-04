# ColorOS 17 native Expressive assets

The current PJZ110 ColorOS 17 target dump already contains a substantial set of resources whose names explicitly identify them as Expressive. A resource-name scan found 133 drawable/mipmap entries containing `expressive` across Settings, SystemUI and framework targets; generated animation frames are included in that raw count.

## Settings category/homepage assets already present

Representative resources:

- `ic_settings_about_device_expressive`
- `ic_settings_accessibility_expressive`
- `ic_settings_accounts_and_backup_expressive`
- `ic_settings_battery_expressive`
- `ic_settings_device_expressive`
- `ic_settings_display_expressive`
- `ic_settings_emergency_expressive`
- `ic_settings_location_expressive`
- `ic_settings_passwords_expressive`
- `ic_settings_privacy_expressive`
- `ic_settings_safety_center_expressive`
- `ic_settings_security_expressive`
- `ic_settings_system_dashboard_expressive`
- `ic_settings_wallpaper_expressive`
- `ic_settings_wireless_expressive`
- `ic_apps_expressive`
- `ic_help_expressive`
- `ic_notifications_expressive`
- `ic_storage_expressive`
- `ic_volume_up_expressive`

## SettingsLib Expressive assets already present

The current Settings package also contains:

- `settingslib_expressive_icon_back`
- `settingslib_expressive_icon_check`
- `settingslib_expressive_icon_chevron`
- `settingslib_expressive_icon_close`
- `settingslib_expressive_icon_collapse`
- `settingslib_expressive_icon_cross`
- `settingslib_expressive_icon_expand`
- `settingslib_expressive_icon_more_vert`
- `settingslib_expressive_icon_up`
- `settingslib_expressive_searchbox_search_icon_24dp`
- `settingslib_expressive_card_background`
- `settingslib_expressive_button_background_filled`
- `settingslib_expressive_button_background_outline`
- `settingslib_expressive_switch_bar_bg`
- `settingslib_expressive_switch_thumb_icon`

## SystemUI assets already present

Representative resources:

- `ic_apps_expressive`
- `ic_check_expressive`
- `ic_chevron_forward_expressive`
- `ic_mic_expressive`
- `ic_phone_expressive`
- `ic_selfie_expressive`
- `ic_touch_expressive`

## Public upstream relationship

AOSP Settings carries the same Expressive resource family and integration pattern. For Android 17 the platform reference branch is `android17-release` under `platform/packages/apps/Settings`.

## Source precedence for v0.2.0

1. `COLOROS_NATIVE_EXPRESSIVE`: keep the current ROM asset when it already exists and has a real consumer.
2. `AOSP_SETTINGS_EXPRESSIVE`: use Android 17 Settings/SettingsLib as the component integration reference.
3. `GOOGLE_MATERIAL_SYMBOL`: use the pinned Material Symbols repository for generic glyph gaps.
4. `KEEP_NATIVE_NON_EXPRESSIVE`: keep OEM/device-specific artwork when no exact expressive equivalent exists.

The mapping problem is therefore consumer-first:

`ColorOS consumer -> native expressive asset? -> AOSP expressive reference? -> Material Symbol fallback`

Do not replace a correct existing Expressive resource with a merely similar Material Symbol.
