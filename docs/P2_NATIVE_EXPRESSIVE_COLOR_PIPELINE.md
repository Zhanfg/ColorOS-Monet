# Native EXPRESSIVE palette experiment — blocked pending hard analysis

ColorOS 17 UXDesign clearly exposes Monet/Material style concepts including `EXPRESSIVE` and `TONAL_SPOT`, but the complete ownership and regeneration flow is still under hard analysis.

Therefore the clean v0.2.0 shipping module **does not mutate**:

`Settings.Secure.theme_customization_overlay_packages`

and does not ship the earlier `coloros17-expressive-style` helper.

The previous helper has been moved to an experiment-only location for reference. It must not return to the shipping module until the Codex report proves:

1. the real style/variant mapping;
2. which component owns palette regeneration;
3. whether changing the Settings.Secure JSON is sufficient;
4. how to respect later user theme changes.

Until then, the shipping semantic layer only consumes the ROM's already-active `system_primary_light/dark` values.
