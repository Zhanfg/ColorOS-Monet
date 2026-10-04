# Verified Material Symbols capability envelope

Pinned upstream:

`google/material-design-icons@737e3324305806514d7909874fa1818ae1808232`

The current ColorOS mapping references **57 distinct Material Symbols**.

CI now inspects the full Android subtree for every mapped symbol instead of
checking only the one requested 24 px asset.

## Verified result

For all **57 / 57** currently mapped symbols, the pinned Rounded family exposes:

- base 20 px
- base 24 px
- base 40 px
- base 48 px
- FILL=1 variants at 20/24/40/48 px
- GRAD=200 at the mapped 24 px size

The CI capability matrix contains:

- 57 required asset checks;
- 456 optional capability checks;
- 456 / 456 optional assets present.

This means the current mapped glyph set is technically capable of MD3E-style
state and optical-size treatment without changing semantic glyph identity.

## What this does not authorize

Technical availability is not component semantics.

Do not automatically use FILL=1 simply because the asset exists.

A row may become `STATEFUL_SYMBOL` only when the real ColorOS component has a
verified selected/unselected or active/inactive state and the same glyph
semantic should persist across that state change.

For ordinary actions such as delete/save/cancel, use the base glyph unless the
component contract explicitly says otherwise.

## Optical size rule

When a verified component slot is 20/40/48 dp, use the matching upstream
optical-size asset. Never scale the 24 px vector merely for convenience.

The generated source of truth remains the CI artifact:

`material-symbols-mapped-capabilities.tsv`
