# Current ColorOS 17 Settings Expressive wrapper proof

The current PJZ110 ColorOS 17 `Settings.apk` has now been inspected at the
compiled XML level, not only by resource-name matching.

All **12 native Expressive wrappers used by the homepage bridge experiment**
are real `com.android.settings.widget.TintDrawable` resources in the current
target.

Each wrapper directly binds:

1. an existing filled Settings glyph;
2. a homepage semantic foreground color.

Examples:

- `ic_settings_about_device_expressive`
  -> `ic_settings_about_device_filled`
  + `homepage_about_foreground`
- `ic_settings_battery_expressive`
  -> `ic_settings_battery_filled`
  + `homepage_battery_foreground`
- `ic_settings_display_expressive`
  -> `ic_settings_display_filled`
  + `homepage_display_foreground`
- `ic_settings_privacy_expressive`
  -> `ic_settings_privacy_filled`
  + `homepage_security_foreground`
- `ic_volume_up_expressive`
  -> `ic_volume_up_filled`
  + `homepage_sound_foreground`

The machine-readable current-target mapping is:

`compat/material-symbols/coloros17_settings_expressive_wrappers.tsv`

## Why this matters

This closes an important distinction:

The native ColorOS/AOSP Expressive icon family is **not a second glyph pack**.
It is a semantic wrapper around the existing filled icon geometry.

That means the preferred homepage pipeline is:

```text
existing Settings filled glyph
        ↓
current target TintDrawable Expressive wrapper
        ↓
homepage semantic foreground role
        ↓
OPlus/native container treatment
```

For the 12 rows where this wrapper already exists, importing a Google Material
Symbol would be a regression in source fidelity.

Material Symbols remain useful for the six homepage generic gaps where the
current target has no equivalent Expressive wrapper.

## Evidence boundary

The wrapper structure and referenced resource names are directly verified from
the user's current Settings APK.

Final on-device appearance is still gated on the native Settings Expressive A/B
probe because OPlus homepage preference subclasses own the final container and
tint application.
