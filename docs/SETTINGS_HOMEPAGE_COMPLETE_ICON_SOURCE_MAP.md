# Complete OPlus Settings homepage icon source map

The OPlus homepage consumer has now been enumerated from
`res/xml/top_level_settings_oplus.xml`.

There are **42 icon-bearing homepage rows** in the current PJZ110 ColorOS 17
Settings build.

Every row now has an explicit source decision in:

`compat/material-symbols/settings_homepage_full_source_map.tsv`

The map deliberately separates two concepts:

- **preferred source**: what v0.2.0 should actually use;
- **Material Symbol fallback**: the exact upstream generic glyph we can use if
  the native/OEM path later becomes unavailable or is intentionally replaced.

## Current source split

The source policy is conservative:

- OEM/product/service-specific rows remain `KEEP_NATIVE`;
- rows with a current native ColorOS/AOSP Expressive asset use
  `NATIVE_EXPRESSIVE`;
- only generic Android semantics with no better native Expressive counterpart
  use `MATERIAL_SYMBOL`.

This prevents the existence of a Google glyph from becoming an excuse to erase
ColorOS-specific identity.

## Why this is stronger than name matching

The rows are keyed by the actual OPlus homepage preference XML. Each row carries
the current icon resource, controller semantics and existing OPlus tint
ownership from the static Settings analysis.

Material Symbols are therefore fallback/candidate assets for a known consumer,
not guesses based only on similar filenames.

## Shipping status

`PROBE_READY` does **not** mean shipping enabled. It means:

- the consumer is known;
- the source asset exists;
- the semantic match is high enough for an isolated visual probe.

The shipping module remains unchanged until on-device visual verification
confirms that the OPlus two-tone/container treatment remains correct.
