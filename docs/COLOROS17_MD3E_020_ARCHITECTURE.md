# ColorOS 17 native-first × Material 3 Expressive architecture (v0.2.0)

## Goal

The project is no longer trying to make ColorOS look like a Pixel skin.

The target is:

> Preserve the parts of ColorOS 17 that are already strong — grouping, blur, OEM motion, card hierarchy, icons, task surfaces and SystemUI behavior — then add Material 3 Expressive where it improves semantics, color, state, typography and prominent interactions.

## Important discovery from the ColorOS 17 dump

The current Android 17 Settings package already contains a substantial native SettingsLib Material 3 Expressive implementation.

Confirmed symbols/resources include:

- `FLAG_IS_EXPRESSIVE_DESIGN_ENABLED`
- `settingslib_expressive_preference`
- `settingslib_expressive_preference_card`
- `settingslib_expressive_preference_category`
- `settingslib_expressive_preference_switch`
- `settingslib_expressive_preference_two_target`
- `settingslib_expressive_preference_dropdown`
- `settingslib_expressive_main_switch_bar`
- `settingslib_expressive_layout_slider`
- `settingslib_expressive_preference_segmentedbutton`
- `homepage_preference_expressive`

This changes the implementation strategy. We should expose and scope the platform's own expressive components where they fit instead of recreating M3E by globally rewriting COUI list geometry.

## Why the old visual system broke

The legacy overlay family modifies shared COUI tokens across 17 target APKs.

Examples:

| Token | ColorOS 17 native | Legacy override |
|---|---:|---:|
| `coui_round_corner_m` | 12dp | 16dp |
| `coui_round_corner_m_radius` | 9dp | 4dp |
| `coui_round_corner_s` | 8dp | Launcher: 20dp |
| `coui_list_divider_height` | 0.33dp | 0dp |
| `coui_popup_list_group_divider_height` | 4dp | SystemUI: 0dp |
| `widget_popup_group_divider_height` | Launcher: 4dp | 0dp |
| `coui_color_divider` | #1f000000 / #33ffffff | transparent |

That turns a local visual preference into a package-wide geometry mutation.

COE then adds package-wide CardHook/ListHook behavior on top, making unrelated screens inherit segmented-card semantics.

## Native ColorOS 17 geometry is already coherent

Representative current values:

- preference card radius: 12dp
- preference horizontal margin: 16dp
- list divider: 0.33dp
- list-card head/tail padding: 2dp
- popup group divider: 4dp with 12dp total group spacing
- medium COUI corner: 12dp
- small COUI corner: 8dp
- XL COUI corner: 20dp

These values are internally consistent. v0.2.0 therefore treats them as the base geometry rather than replacing them globally.

## MD3E integration model

### Layer 1 — ColorOS native shell

Keep:

- COUI list grouping
- popup/menu grouping
- blur and translucent surfaces
- OEM navigation behavior
- native SystemUI geometry
- native icon glyphs
- device-specific motion where it is already better integrated

### Layer 2 — semantic dynamic color

Map roles, not arbitrary resource names:

- page background
- surface/container
- elevated surface
- selected container
- on-surface content
- outline/divider
- state layer
- primary/secondary/tertiary accents

Do not collapse multiple native roles into one Monet color.

### Layer 3 — native SettingsLib Expressive

Use Android 17's own expressive resources for components that actually benefit from it:

- prominent preference cards
- main switches
- sliders
- button groups
- intentional segmented groups
- selected homepage surfaces

Do not use expressive-card geometry for every preference row.

### Layer 4 — scoped hooks

Hooks must be scoped by screen/component and class capability.

No more package-wide "all preferences become cards".

A hook must:

1. identify the exact component family;
2. verify the expected ColorOS 17 class/method/field shape;
3. fall back to native behavior if the capability is absent;
4. never mutate shared COUI resources globally.

## Motion policy

Material 3's current MotionScheme separates spatial motion from effects motion.

Use:

- standard motion for recurring/utilitarian Settings interactions;
- expressive motion for prominent QS/media/hero surfaces;
- spatial specs for bounds/shape changes;
- effects specs for color/alpha/state-layer changes.

ColorOS native blur/motion wins when replacing it would reduce coherence or performance.

## Release plan

### P0 — structural correctness

- ban shared COUI geometry/divider overrides;
- restore native list and popup group semantics;
- remove package-wide CardHook/ListHook behavior;
- keep existing ColorOS 17 shape hierarchy.

### P1 — semantic MD3E

- rebuild dynamic color role mapping;
- selectively expose native SettingsLib Expressive components;
- unify state layers;
- normalize typography roles without changing layout-critical metrics.

### P2 — SystemUI

- audit QS, media, volume and notifications independently;
- keep component-specific radii;
- preserve ColorOS blur;
- apply expressive motion only where appropriate.

### P3 — validation

Visual regression matrix:

- light / dark
- wallpaper dynamic color variants
- Settings home
- ordinary second-level Settings page
- About device
- permission/install dialogs
- launcher popup/folder/recent tasks
- notification shade
- QS/control center
- media
- volume

## Repository guard

`tools/audit_coloros17_ui_tokens.py` blocks accidental reintroduction of the shared-token mutations that caused the current visual regression.

The machine-readable baseline and policy are in:

- `compat/coloros17/native_baseline.json`
- `compat/coloros17/md3e_policy.json`
