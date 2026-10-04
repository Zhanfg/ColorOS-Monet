# Native Expressive pairing audit

The current ColorOS 17 resource snapshot contains 133 drawable/mipmap entries whose names include `expressive`.

After excluding generated animation-frame internals, 109 named resources remain. A strict sibling-name analysis proves **36 direct base -> Expressive pairs** without guessing consumer behavior.

Examples:

- `ic_apps -> ic_apps_expressive`
- `ic_help -> ic_help_expressive`
- `ic_notifications -> ic_notifications_expressive`
- `ic_settings_display -> ic_settings_display_expressive`
- `ic_settings_location -> ic_settings_location_expressive`
- `ic_settings_privacy -> ic_settings_privacy_expressive`
- `ic_settings_security -> ic_settings_security_expressive`
- `ic_settings_wireless -> ic_settings_wireless_expressive`
- `ic_storage -> ic_storage_expressive`
- `settingslib_card_background -> settingslib_expressive_card_background`
- `settingslib_switch_bar_bg -> settingslib_expressive_switch_bar_bg`
- SystemUI `ic_check -> ic_check_expressive`
- SystemUI `ic_touch -> ic_touch_expressive`

The remaining **73 named Expressive resources** do not have a trivial same-package sibling obtained only by removing the word `expressive`. They are kept in a separate inventory and must be resolved by consumer tracing, AOSP Settings/SettingsLib reference, or exact Material Symbol matching.

This distinction matters: an Expressive resource existing in the APK does not prove which screen consumes it.

Generated metadata:

- `compat/material-symbols/native_expressive_pairs.tsv`
- `compat/material-symbols/native_expressive_unmatched.tsv`

Reproduce locally with:

```sh
python tools/build_native_expressive_pairs.py \
  --aapt2 /path/to/aapt2 \
  --targets /path/to/ColorOS17_TargetDump/files/targets \
  --pairs /tmp/native_expressive_pairs.tsv \
  --unmatched /tmp/native_expressive_unmatched.tsv
```
