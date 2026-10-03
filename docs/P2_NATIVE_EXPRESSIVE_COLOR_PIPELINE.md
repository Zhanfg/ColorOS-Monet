# P2: use ColorOS 17's native EXPRESSIVE Monet variant

The current ColorOS 17 UXDesign package (17.0.15) already ships the Google/libmonet dynamic-color stack and exposes native variants including:

- EXPRESSIVE
- TONAL_SPOT
- SPRITZ
- VIBRANT
- MONOCHROMATIC

The live device baseline stores the current selection in:

`Settings.Secure.theme_customization_overlay_packages`

with:

`"android.theme.customization.theme_style":"TONAL_SPOT"`

UXDesign also contains the user-facing wallpaper color labels for the variants; the Chinese label for EXPRESSIVE is “饱满” (“Bright” in the default resource).

## Design decision

v0.2.0 should not synthesize a second independent Monet palette engine.

Instead it requests the ROM's own `EXPRESSIVE` variant while preserving:

- the existing wallpaper color source;
- ColorOS generated dynamic overlays / FRROs;
- OEM blur/translucent composition;
- other theme JSON fields.

The helper stores only the previous theme-style enum and restores it on uninstall **only if** the current style is still EXPRESSIVE, so a later manual user theme choice is not overwritten.

This makes the color layer genuinely native-first: ColorOS generates the palette; the module focuses on correcting legacy geometry/surface overrides and on component-scoped expressive behavior.
