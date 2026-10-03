# ColorOS 17 × Material 3 Expressive 2026 UI audit

Baseline: PJZ110 / Android 17 / ColorOS 17 internal build.
Public Material baseline used for this audit: Compose Material3 1.4.0 stable and 1.5.0-alpha29 (2026-09-23).

## Executive finding

The current module applies several **global COUI token overrides** and COE applies a **global segmented-card hook**. That combination is the main reason many unrelated pages look like a stack of small rounded cards.

This is not a single Settings/About-device defect. It is a cross-package design-system defect.

## P0 confirmed defects

### 1. Global list dividers are removed

Legacy overlays override shared COUI resources such as:

- `coui_list_divider_height = 0dp`
- `coui_color_divider = transparent`
- `coui_popup_list_group_divider_height = 0dp`
- `coui_popup_list_group_divider_color = transparent`
- Launcher `widget_popup_group_divider_height = 0dp`

On the current ColorOS 17 targets, representative native values are:

- `coui_list_divider_height = 0.33dp`
- `coui_popup_list_group_divider_height = 4dp`
- `coui_popup_list_group_divider_total_height = 12dp`
- Launcher `widget_popup_group_divider_height = 4dp`
- `coui_color_divider` is non-transparent in light and dark themes.

Affected legacy overlays include Settings, WirelessSettings, NotificationManager, Launcher, Permission, PhoneManager and all SystemUI variants, with related overrides in additional apps.

### 2. Shared COUI corner tokens are overwritten with incompatible values

Representative native ColorOS 17 values:

- `coui_round_corner_m = 12dp`
- `coui_round_corner_m_radius = 9dp`
- `coui_round_corner_s = 8dp`

Legacy overlay examples:

- `coui_round_corner_m = 16dp`
- `coui_round_corner_m_radius = 4dp`
- Launcher `coui_round_corner_s = 20dp`

These are framework-style shared resources used by multiple component families, so changing them globally changes list items, popups, cards, menus and other surfaces at once.

### 3. COE globally applies segmented-card behavior

COE 2.9.3 contains:

- `CardHook`
- `ListHook`
- `enable_card_hook`
- `remove_card_divider`
- "Enable Expressive segmented cards and the Settings home account item style"
- "Remove dividers in setting item cards"

The same binary also contains a compatibility note saying the segmented backgrounds/content/interaction implementation is supported on OxygenOS 16.0.8–16.0.10.

On ColorOS 17 this must not be treated as a universal replacement for every preference row.

## Material 3 Expressive interpretation

Latest Material 3 Expressive exposes both ordinary `ListItem` and `SegmentedListItem`.

`SegmentedListItem` is a distinct component with:

- explicit item index/count
- index-dependent shapes
- a defined `SegmentedGap`
- state-dependent shape morphing
- content-line-dependent minimum height

Therefore "Material Expressive" does **not** mean "convert every list row in the OS to a standalone rounded segment".

Policy for ColorOS 17:

1. Standard preference/settings groups: preserve continuous grouped-list semantics and native separators.
2. Segmented lists: use only for intentionally segmented, high-emphasis groups where item count and first/middle/last geometry are known.
3. Menus/popups: use expressive menu-specific shapes/colors, not list-card geometry.
4. SystemUI tiles/media/volume: component-specific expressive geometry only.
5. Never change global COUI geometry tokens to force a local component appearance.

## P1 color hierarchy defects

The old RRO maps a large set of distinct ColorOS surface roles onto Android dynamic-color roles. Dynamic color itself is correct, but role collapsing is too broad.

Examples:

- background-with-card -> `system_surface_container`
- card background -> `system_surface_bright`
- surface-top / surface-with-card / elevated-with-card -> `system_surface_container_low`

The new implementation must preserve semantic tonal hierarchy rather than recoloring every neutral surface with a small set of shared values.

Required mapping policy:

- page background
- grouped container
- elevated container
- selected/active container
- pressed/state layer
- divider/outline
- content/on-surface

must remain distinct roles.

## P1 typography

The RRO itself barely changes typography, while COE selectively changes large titles and SystemUI fonts (including Google Sans Flex Rounded / variable-font settings).

This creates a partial typography system rather than one coherent Material type system.

Policy:

- keep ColorOS text metrics where layout depends on them;
- use expressive type roles only where the hook owns the complete component;
- do not globally replace text size/line height;
- variable-font animation is acceptable for hero/system UI interactions, not utilitarian preference rows.

## P1 motion

Material 3 Expressive now defines a MotionScheme with separate spatial/effects motion:

- spatial motion for bounds/shape changes;
- effects motion for color/alpha;
- fast/default/slow tiers.

Current module has independent springs, ripple keep-alive logic and component-specific animations but no single motion-role policy.

Policy:

- shape/bounds morph -> spatial spec;
- tint/alpha/ripple -> effects spec;
- repeated Settings rows -> standard/utilitarian motion;
- hero interactions (QS, media, prominent surfaces) -> expressive motion.

## P1 component policy

### Settings / WirelessSettings / Battery / Permission / PhoneManager
- default to continuous grouped lists;
- restore dividers and native grouping;
- dynamic-color semantic surfaces;
- no universal per-row segmented card.

### Settings home
- may use stronger expressive containers;
- account/header/high-priority destinations can use segmented treatment;
- section groups must be structurally coherent.

### Launcher
- popup/menu geometry must use menu/popup tokens;
- restore widget popup group separator;
- do not reuse generic Settings-card shapes.

### SystemUI
- QS tiles, volume, notifications, media are independent component systems;
- notification radius must not be changed globally just to match settings cards;
- current ColorOS 17 notification radius is 16dp while the legacy overlay uses 18dp.

### Dialogs / popups
- restore group separators;
- use component-specific containers and state layers;
- avoid a universal transparent-divider policy.

## Implementation order

P0:
1. Remove global divider suppression from ColorOS 17 compatibility overlays.
2. Stop overriding global `coui_round_corner_*` tokens for local visual goals.
3. Gate COE CardHook/ListHook by component/screen instead of package-wide.
4. Preserve native ColorOS 17 grouping for ordinary preference lists.

P1:
5. Rebuild semantic surface mapping.
6. Introduce contextual segmented-list policy.
7. Normalize menu/dialog/popup tokens.
8. Align motion and typography policies.

P2:
9. Audit SystemUI-specific expressive geometry.
10. Per-screen visual regression snapshots in light/dark + dynamic-color variants.

## Release note

This is no longer a narrow Android-17 compatibility patch. It changes the visual architecture across the module and should be treated as a medium feature update rather than another hotfix.
