# Icon source resolver

Icon selection is now explicit and ordered:

1. exact ColorOS native Expressive sibling;
2. curated ColorOS native Expressive candidate;
3. Google Material Symbol candidate;
4. keep the native non-Expressive drawable.

No stage emits artwork automatically.

The resolver produces a decision table that still carries a consumer-trace gate.
This prevents resource-name similarity from becoming a shipping replacement.

Important examples already resolved by precedence:

- Settings `ic_help`: native `ic_help_expressive` wins over Material Symbol `help`.
- Settings `ic_storage`: native `ic_storage_expressive` wins over Material Symbol `storage`.
- Settings `ic_notifications`: native `ic_notifications_expressive` wins over Material Symbol `notifications`.
- Settings `ic_settings_security`: native `ic_settings_security_expressive` wins over Material Symbol `security`.

Material Symbols remain valuable as a complete fallback/reference catalog, but they do not override an already-present ColorOS Expressive asset.


## OPlus homepage hard exclusion

The resolver now accepts the derived
`settings_oplus_homepage_icons.tsv` inventory. Any icon owned by that XML is
resolved as:

`KEEP_NATIVE_OPLUS_HOMEPAGE`

with gate:

`VERIFIED_OPLUS_XML_AND_DEX_OWNER`

before native Expressive or Material Symbol precedence is considered.

This prevents future automatic catalog expansion from accidentally replacing
ColorOS homepage glyphs that are already part of the vendor two-tone pipeline.
