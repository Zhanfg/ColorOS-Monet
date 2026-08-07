# Clean-room rebuild record

## Inputs used as behavior references

Historical overlay packages were inspected only to identify:

- target package names;
- target resource identifiers and configuration qualifiers;
- primitive resource values;
- high-level container behavior such as selector, shape, layer list, and animation category.

## Excluded material

The repository and generated packages do not copy:

- APK bytecode or native libraries;
- original Binary XML files;
- vector `pathData` from third-party packages;
- PNG/WebP artwork;
- signing certificates or private keys.

## Reimplementation strategy

- Material color roles are mapped to public Android dynamic palette resources.
- Known icons are redrawn from a small project-owned geometric vocabulary.
- Unknown proprietary images receive neutral project-owned fallback glyphs.
- Safe shape and selector behavior is reconstructed from semantic structure.
- Path-morph animations are replaced with a project-owned alpha transition.
- Build-time text XML is compiled into Binary XML; temporary APKs are discarded.

## Coverage

- 37 historical binary targets are represented as independently authored component specs.
- X, TIM, and Coolapk are converted from reviewed semantic mapping tables.
- Total package count: 40.

Entries that cannot be represented safely are listed per component in `unsupported.tsv`. These are not silently declared compatible.
