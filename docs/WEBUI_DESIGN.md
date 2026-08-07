# Future WebUI design direction

## Inspiration statement

The information hierarchy and dark-surface treatment are inspired by the COUI Expressive / Material 3 Expressive community interfaces supplied by the project owner. No image, avatar, icon asset, layout file, or implementation code is copied.

## Proposed screens

1. **Overview**
   - current palette preview;
   - runtime status and last apply time;
   - installed, enabled, failed, and policy-blocked counts.
2. **Component catalog**
   - rounded component cards grouped by ColorOS, WeChat, Scene, and Applications;
   - target package state;
   - enable switch and compatibility badge;
   - exclusive-style selector for SystemUI and WeChat bubble variants.
3. **Component detail**
   - `CMONET01` header and digest state;
   - target package, backend, resource count, unsupported count;
   - apply log and rollback action.
4. **Diagnostics**
   - OverlayManager state;
   - policy rejection reason;
   - palette fingerprint changes;
   - exportable redacted report.

## Visual rules

- use dynamic accent colors rather than fixed brand blue;
- use layered dark surfaces instead of pure-black cards everywhere;
- preserve readable contrast for primary, secondary, and disabled text;
- use large rounded cards and compact segmented controls;
- do not reproduce the reference screenshots' avatars, names, group data, or artwork.
