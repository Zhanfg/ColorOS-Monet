# Material Symbols matching policy

The upstream is pinned in `compat/material-symbols/upstream.lock`.

## Two-stage process

### Stage 1 — candidate generation

Run the local ColorOS target dump through:

`tools/extract_coloros_icon_inventory.py`

Then run:

`tools/suggest_material_symbol_matches.py`

against the pinned Google Material Symbols checkout.

This stage is mechanical. It produces up to three candidates and never modifies
the shipping module.

### Stage 2 — semantic review

A candidate can enter `coloros_icon_map.tsv` only after checking the real
consumer/component meaning.

A name match is not sufficient evidence.

Examples:

- `ic_back` → `arrow_back`: normally a high-confidence generic action.
- `device_market_name_phone_icon`: keep native unless an exact product-neutral
  replacement is proven.
- Wi-Fi RSSI level assets: state-machine assets, not individual icons to replace
  one-by-one.
- fingerprint / charging / OPlus personality assets: OEM-specific by default.

## Family

`materialsymbolsrounded` is the first candidate for ColorOS integration, but
not a global requirement. Outlined or Sharp may be chosen if the surrounding
native component makes them a better optical fit.

## Size

Use the upstream optical-size asset that matches the actual Android component
slot. Do not take a 24 px path and blindly scale it for 20/40/48 dp slots.

## Stateful icons

A `fill1` asset is only a **candidate** selected state. Do not assume it changes
the glyph merely because the file exists.

A mapping may use `base → fill1` only when:

1. the ColorOS consumer actually owns a selected/unselected state;
2. both pinned upstream assets exist;
3. the selected XML differs from the base XML;
4. visual review confirms that the transition fits the component.

If base and `fill1` are byte-identical, treat the symbol as a static glyph and
leave state/tint ownership to ColorOS/OPlus.

See `docs/MATERIAL_SYMBOLS_STATE_AXIS.md`.

## Shipping rule

`NEEDS_REVIEW` rows are documentation only and must never be emitted into an
RRO automatically.


## OPlus Settings homepage exclusion

The current ColorOS 17 `top_level_settings_oplus.xml` has its own icon-treatment contract:
41/42 icon-bearing preferences opt into OPlus two-tone handling and none directly references a `*_expressive` icon name.

Therefore the Settings homepage must not be bulk-generated from Material Symbols.
Material Symbols may only fill an individually verified glyph gap after the OPlus preference consumer is traced.

See `docs/COLOROS17_OPLUS_HOMEPAGE_ICON_PIPELINE.md`.


## Settings homepage exception

Current ColorOS 17 Settings homepage category wrappers are already proven to
embed native Expressive foreground glyphs inside 24dp categorical containers.

For these resources, the source decision is final:

`KEEP_NATIVE_WRAPPER`

Material Symbols must not replace `ic_homepage_*` category wrappers.

See `docs/SETTINGS_HOMEPAGE_ICON_ARCHITECTURE.md`.
