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

When the UI has a selected/unselected state and the same Material Symbol exposes
a FILL variant, prefer a stateful mapping:

`base → fill1`

instead of swapping unrelated glyphs.

## Shipping rule

`NEEDS_REVIEW` rows are documentation only and must never be emitted into an
RRO automatically.
