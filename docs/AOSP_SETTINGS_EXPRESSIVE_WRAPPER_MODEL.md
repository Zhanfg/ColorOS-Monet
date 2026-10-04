# AOSP Settings Expressive wrapper model

Public AOSP Settings history shows that the homepage Expressive icon migration
did not create a second independent glyph system.

For many Settings homepage categories the Expressive resource is a
`com.android.settings.widget.TintDrawable` wrapper around the already-existing
filled drawable, with a category-specific foreground color.

Examples:

- `ic_settings_about_device_expressive` wraps
  `ic_settings_about_device_filled` and uses `homepage_about_foreground`.
- `ic_settings_battery_expressive` wraps
  `ic_settings_battery_filled` and uses `homepage_battery_foreground`.
- `ic_settings_security_expressive` wraps
  `ic_settings_security_filled` and uses `homepage_security_foreground`.
- `ic_volume_up_expressive` wraps `ic_volume_up_filled` and uses
  `homepage_sound_foreground`.

The same AOSP change switches homepage layer-list consumers from older
white/base drawables to the new `*_expressive` resources.

## Consequence for ColorOS-Monet

For Settings homepage icons, the preferred implementation is **not** to import a
new Material Symbol when ColorOS 17 already contains the corresponding
Expressive wrapper family.

The likely safe direction is:

`existing filled glyph geometry -> native/AOSP Expressive wrapper -> semantic tint role`

The exact ColorOS 17 runtime consumer remains gated on the Codex Settings report.
This public AOSP evidence is therefore architecture guidance, not proof that
ColorOS executes the identical source path.

Derived mapping data is stored in:

`compat/material-symbols/aosp_settings_expressive_wrappers.tsv`
