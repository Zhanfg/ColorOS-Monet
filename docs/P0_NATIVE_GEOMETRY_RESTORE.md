# P0: native geometry restoration

This layer reverses global geometry/divider overrides from the legacy module when running on the current ColorOS 17 baseline.

It intentionally restores native ColorOS 17 values for shared COUI tokens before any MD3E component-scoped enhancement is applied.

## Why

The legacy overlays changed shared resources such as:

- coui_color_divider -> transparent
- coui_list_divider_height -> 0dp
- coui_round_corner_m -> 16dp
- coui_round_corner_m_radius -> 4dp
- launcher coui_round_corner_s -> 20dp
- widget popup group divider -> 0dp
- OPlus toast radius -> 100dp
- SystemUI notification radius -> 18dp
- SystemUI volume row radius -> 23dp by overriding the base token

On ColorOS 17, those values are part of shared component families. Applying them globally causes unrelated pages to inherit the same card geometry.

## Strategy

1. Keep the legacy payload untouched for compatibility.
2. Add a higher-priority static RRO per affected target.
3. Restore only the shared/native geometry and divider tokens listed in compat/coloros17/native_restore.tsv.
4. Add MD3E later through screen/component-scoped hooks and semantic color resources, never by mutating shared COUI geometry globally.

The table contains only resource identifiers and independently observed native values from the user's current ROM baseline; no proprietary artwork is stored.
