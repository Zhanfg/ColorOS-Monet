# Material Symbol state and optical-size capability policy

Material 3 Expressive icon work should prefer one semantic glyph that can
express state through the upstream Material Symbols axes/variants instead of
swapping unrelated artwork.

The upstream verifier now records, for every mapped symbol:

- required mapped asset;
- optional `fill1` asset at the mapped size;
- optional `grad200` asset;
- base assets at 20/24/40/48 px;
- `fill1` assets at 20/24/40/48 px.

These optional results are review evidence only.

They do **not** automatically change a mapping from `NEEDS_REVIEW` to
`STATEFUL_SYMBOL`.

A stateful mapping still requires a real component with a selected/unselected
or active/inactive state whose semantics remain the same across the transition.

Examples of valid future use:

- selected navigation/settings category: base → fill1;
- active toggle affordance when the glyph semantic itself stays unchanged.

Examples that must not be inferred merely from capability:

- delete/cancel/save action icons;
- OEM feature icons;
- signal-strength state machines;
- notification state icons with component-owned animation.

The generated CI artifact
`material-symbols-mapped-capabilities.tsv` is the authoritative capability
matrix for the pinned Google upstream revision.
