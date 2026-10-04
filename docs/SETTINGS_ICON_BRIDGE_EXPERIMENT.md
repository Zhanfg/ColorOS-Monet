# Settings native Expressive + Material Symbols bridge experiment

Codex closed the Settings ownership model:

- OPlus homepage XML and preference subclasses own homepage row icon/tint semantics.
- SettingsLib owns the native Expressive grouped-list adapter path when the native gate is active.
- Material Symbols must remain a fallback for generic glyph gaps, not a replacement for the whole homepage.

This experiment tests only the **inner glyph source**.

## Modes

`native`

Redirect rows already classified `NATIVE_EXPRESSIVE` to the exact
`*_expressive` drawable already present in the installed ColorOS 17 Settings APK.

`material`

Replace only rows classified `MATERIAL_SYMBOL_CANDIDATE` with the pinned
official Google Material Symbols Rounded 24px base glyph.

`combined`

Apply both sets.

The OPlus preference class still owns tint/two-tone/container behavior.

## Important

This RRO is unsigned and experiment-only. It is not included in the shipping
module and is not automatically enabled.

The builder requires the local Settings APK so private target references are
resolved without copying vendor artwork into the public repository.

## Native Settings Expressive gate probe

`experiments/ColorOS17_SettingsNativeExpressive_Toggle_v1.sh`

temporarily toggles the already-proven debug property
`is_expressive_design_enabled`.

It:

- uses no arguments;
- writes only the non-persistent property;
- does not reboot;
- does not force-stop Settings;
- does not touch `theme_customization_overlay_packages`;
- restores the first observed property value when run again.

This is intended to determine whether ColorOS 17's existing SettingsLib
Expressive adapter/layout path is visually viable before any permanent hook is
designed.
