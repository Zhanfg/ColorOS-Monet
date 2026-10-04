# Official Material Symbols upstream for ColorOS 17 / MD3E

## Canonical public upstream

Repository:

`google/material-design-icons`

Pinned snapshot for this project:

`737e3324305806514d7909874fa1818ae1808232`

Commit message: `Update Symbols`  
Commit date: 2026-10-02.

This is Google's current public Material Symbols distribution. The classic
Material Icons set in the same repository is legacy; new work should use
`symbols/` and `variablefont/`.

## Important distinction: Material 3 Expressive does not have a separate icon repo

Material 3 Expressive changes component sizing, shape, motion, state treatment
and composition. Its iconography continues to use **Material Symbols**.

Therefore our icon source of truth is Material Symbols, while MD3E behavior is
implemented at the component layer.

Do not look for or invent a separate "MD3E icon pack".

## What is available upstream

At the pinned snapshot, `symbols/android/` contains **4,150 symbol-name
directories**.

Each symbol may expose Android VectorDrawable assets in one or more families:

- `materialsymbolsrounded`
- `materialsymbolsoutlined`
- `materialsymbolssharp`

Typical static sizes include:

- 20 px
- 24 px
- 40 px
- 48 px

Many symbols also expose generated variants such as:

- `fill1`
- `grad200`
- weight/grade/optical-size variants where generated

The full variable fonts are under `variablefont/` and expose:

- FILL
- GRAD
- opsz
- wght

## Default family for this project

For new MD3E augmentation on ColorOS 17, the default candidate family is:

`Material Symbols Rounded`

This is a **candidate default, not a global replacement rule**.

ColorOS native artwork remains preferred when it already communicates the
correct meaning and is part of an OEM-specific visual identity.

## Replacement policy

### KEEP_NATIVE

Use the ColorOS drawable unchanged when:

- it is OEM/product-specific;
- it carries layered alpha, brand/device identity or custom geometry;
- Material Symbols has no exact semantic equivalent;
- replacing it would reduce information density or recognizability.

### MATERIAL_SYMBOL_CANDIDATE

Consider an upstream Material Symbol when:

- the icon represents a generic Android/system action;
- an exact semantic equivalent exists upstream;
- the surrounding component is being brought into MD3E;
- the replacement does not break OEM-specific meaning.

### STATEFUL_SYMBOL

For selected/unselected states, prefer the same Material Symbol with a state
axis/variant (for example FILL 0 → 1) rather than unrelated artwork.

### NO_APPROXIMATE_MATCH

Never replace a ColorOS icon merely because another symbol looks visually
similar. Every mapping must record semantic confidence and evidence.

## Mapping schema

The mapping table is:

`compat/material-symbols/coloros_icon_map.tsv`

Columns:

- target_package
- target_resource
- semantic_role
- material_symbol
- family
- size
- unselected_variant
- selected_variant
- action
- confidence
- notes

Allowed actions:

- `KEEP_NATIVE`
- `MATERIAL_SYMBOL`
- `STATEFUL_SYMBOL`
- `NEEDS_REVIEW`

## Workflow

1. Extract the target ColorOS 17 drawable/resource name.
2. Determine semantic meaning from its real consumer, not only the resource name.
3. Search the pinned Material Symbols index.
4. Compare Rounded / Outlined / Sharp candidates.
5. Compare 20/24/40/48 optical-size assets when relevant.
6. Prefer native artwork unless the Material Symbol is an exact semantic fit.
7. Store the decision in the mapping table.
8. Only generate an Android overlay after the mapping is reviewed.

## Licensing

The Google Material Symbols / Material Icons repository is distributed under
Apache License 2.0. Keep the upstream license/attribution metadata when
redistributing assets.


## Source precedence with native Expressive assets

Material Symbols remains the canonical generic glyph repository, but it is not
the first replacement source for every ColorOS component.

For the current ColorOS 17 build use:

1. current ColorOS `*_expressive` / `settingslib_expressive_*` resource;
2. AOSP Settings/SettingsLib `android17-release` as the component integration reference;
3. pinned Google Material Symbol as the generic glyph fallback;
4. otherwise keep the native OEM drawable.

See `docs/COLOROS17_NATIVE_EXPRESSIVE_ASSETS.md`.


## SetupDesign / SUD exception

Resources prefixed with `sud_` belong to Android SetupDesign/Glif, not to the
generic Material Symbols catalog. The Android 17 SetupDesign release is pinned
in `compat/material-symbols/setupdesign.source`.

For these resources the source order is:

ColorOS native SUD resource -> AOSP SetupDesign component contract -> keep
native extension.

Do not route a SUD switch/control resource into generic Material Symbol
matching.
