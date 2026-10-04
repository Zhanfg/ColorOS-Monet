# Android 17 Expressive upstream overlap

The ColorOS 17 target resource inventory was compared against two public Android 17 upstreams.

## AOSP Settings

Pinned Settings reference:

`213829fb67f5e070029e0513a088f31bc8f5c1ed`

Result:

- AOSP Settings exposes **41** drawable resources containing `expressive`.
- **All 41/41 names are present in the current ColorOS 17 Settings resources.**

This is strong structural evidence that the current ColorOS Settings package already carries the Android 17 Expressive icon/illustration resource family rather than only a vendor imitation.

## AOSP SettingsLib

Pinned frameworks/base Android 17 reference:

`94b4c163b7dfe5ce3607f7bb8456f9573f7de57d`

The SettingsLib tree contains Expressive component resources for toolbars, switches, buttons, spinners, status banners, cards, search, segmented controls, sliders and preference layouts.

Against the current ColorOS Settings/SystemUI inventory:

- **50 ColorOS package/resource rows** have exact-name SettingsLib matches.
- Those rows represent **36 unique Expressive resource names**.

Examples include:

- `settingslib_expressive_icon_back`
- `settingslib_expressive_icon_check`
- `settingslib_expressive_icon_chevron`
- `settingslib_expressive_icon_close`
- `settingslib_expressive_icon_expand`
- `settingslib_expressive_icon_more_vert`
- `settingslib_expressive_searchbox_search_icon_24dp`
- `settingslib_expressive_switch_thumb_icon`
- `settingslib_expressive_card_background`
- `settingslib_expressive_spinner_background_outlined`

## Consequence for the project

The source order is now stricter:

1. ColorOS native Expressive resource already wired to the component;
2. exact Android 17 AOSP Settings / SettingsLib Expressive reference;
3. pinned Google Material Symbol for a genuine generic-glyph gap;
4. otherwise keep the ColorOS native drawable.

Material Symbols is therefore the complete **generic glyph upstream**, while AOSP Settings/SettingsLib is the more authoritative **Expressive component integration upstream**.

The machine-readable exact-name matches are in:

`compat/material-symbols/aosp_expressive_name_matches.tsv`

Exact-name overlap is structural evidence, not proof that every resource is active on the current screen. Runtime consumer tracing remains the activation gate.
