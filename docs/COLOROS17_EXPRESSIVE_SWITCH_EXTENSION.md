# ColorOS 17 Expressive switch-thumb extension

The current ColorOS 17 Settings and SystemUI packages both extend the public
SetupDesign Expressive switch-thumb family.

## Verified target structure

In both packages:

- `sud_ic_switch_check_mark_expressive` is a 16dp vector checked glyph;
- `sud_ic_switch_uncheck_mark_expressive` is a 16dp vector cross glyph;
- `sud_ic_switch_selector_expressive` is a checked-state selector.

The selector binds the checked glyph when `state_checked=true` and the ColorOS
cross glyph when `state_checked=false`.

The Settings and SystemUI resource IDs differ, but each selector resolves to its
own package-local checked/unchecked resources.

## Architecture decision

`sud_ic_switch_uncheck_mark_expressive` is not a generic Material-Symbol gap.
It is a verified ColorOS extension to the SetupDesign state model.

Decision:

`KEEP_NATIVE`

Do not replace it with `close`, `cancel`, or any other visually similar
Material Symbol.

The native switch component owns the state transition and tint.

## Evidence boundary

This document records dimensions, state semantics and resource relationships
only. Proprietary vector path data is intentionally not copied into the public
repository.
