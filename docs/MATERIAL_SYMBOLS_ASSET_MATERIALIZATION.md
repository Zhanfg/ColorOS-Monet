# Material Symbol asset materialization

The project does not vendor the entire Google Material Symbols repository.

When an icon mapping is eventually promoted from `NEEDS_REVIEW` to either
`MATERIAL_SYMBOL` or `STATEFUL_SYMBOL`, the selected Android VectorDrawable
is copied from the pinned upstream checkout by:

`tools/materialize_material_symbol_assets.py`

The tool:

- ignores every unreviewed mapping;
- copies the official upstream XML without redrawing its geometry;
- records the exact upstream path;
- records the pinned upstream commit;
- records SHA-256 for every copied vector;
- keeps package-specific staging directories separate.

For a stateful symbol the unselected asset is staged under the target resource
name and the selected asset is staged with a `__selected` suffix. Wiring that
state into the target component is a separate, component-scoped step and is
never inferred automatically.

This keeps icon provenance auditable and prevents a generated approximation from
being mistaken for an official Material Symbol.
