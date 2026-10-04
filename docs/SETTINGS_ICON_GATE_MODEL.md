# Settings icon gate model after hard analysis

The previous gate assumed `native_expressive_map.tsv` must never intersect the OPlus
homepage icon domain. That assumption is obsolete.

ColorOS 17 Settings contains two layers:

1. OPlus homepage preferences own the visible row, two-tone/tint policy and current
   `settings_*.xml` glyph selection.
2. Settings also contains verified Android 17/SettingsLib `*_expressive`
   `TintDrawable` wrappers.

Therefore a native Expressive resource may be a **secondary glyph candidate**
for an OPlus homepage row without becoming the current/shipping owner.

The gate now enforces:

- OPlus current glyph remains primary;
- a homepage Expressive candidate must have current-target wrapper provenance;
- importing a wrapper does not transfer tint ownership from OPlus;
- candidate promotion remains behind the native Expressive gate A/B review;
- direct shipping Material-Symbol replacement of an OPlus current homepage glyph
  remains forbidden.

This aligns the static policy with the Codex ownership model and the current
binary-XML wrapper evidence.
