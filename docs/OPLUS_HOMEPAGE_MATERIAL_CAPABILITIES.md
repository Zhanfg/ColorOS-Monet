# OPlus homepage Material Symbol candidate capabilities

The six remaining generic OPlus homepage glyph gaps have now been materialized from the pinned Google Material Symbols revision:

`google/material-design-icons@737e3324305806514d7909874fa1818ae1808232`

All six base 24px Rounded assets exist.

## FILL capability is not uniform

Comparing the exact upstream XML hashes shows:

- `flight`: base == fill1
- `wifi`: base == fill1
- `settings_bluetooth`: base == fill1
- `gavel`: base == fill1
- `lock`: base != fill1
- `manage_accounts`: base != fill1

Therefore the project must not assume that every Material Symbol exposes a visually distinct selected/FILL state merely because a `fill1` file exists.

For the OPlus Settings homepage specifically, ColorOS already owns the outer two-tone/tint category through its preference classes. The initial glyph-swap experiment should use the **base** official glyph and preserve the native OPlus tint pipeline. FILL variants are not used as a substitute for the ColorOS row/category state.

Machine-readable evidence:

`compat/coloros17/settings_homepage_material_capabilities.tsv`

The CI-generated non-flashable review pack contains the exact upstream XML plus SHA-256 hashes.
