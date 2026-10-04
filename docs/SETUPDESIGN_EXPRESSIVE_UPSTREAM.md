# SetupDesign Expressive upstream

The remaining `sud_*` Expressive resources belong to the SetupDesign/Glif
component family rather than SettingsLib or Material Symbols.

## Official Android upstream

Repository:

`platform/external/setupdesign`

Pinned Android 17 release:

- tag: `android-17.0.0_r1`
- release commit: `79dbf5860322236cd02e74e2ca0855591d95195c`

The repository is Apache-2.0 and is the authoritative source family for SUD
(SetupDesign) resources.

## Switch semantics

Public Android 17 SetupDesign confirms the base Expressive switch contract:

- `sud_ic_switch_selector_expressive` is the checked-state selector;
- the checked state references `sud_ic_switch_check_mark_expressive`;
- the checked glyph is a 16dp vector themed by `?attr/colorPrimary`;
- `SwitchItem.updateThumbIconDrawable(...)` installs the selector on the
  checked path;
- the public unchecked path sets the MaterialSwitch thumb icon to `null`.

Current ColorOS 17 extends that public contract. Settings and SystemUI both
contain a local:

`sud_ic_switch_uncheck_mark_expressive`

and their local `sud_ic_switch_selector_expressive` resources explicitly bind
that cross glyph to `state_checked=false`.

## Project decision

- selector/check resources are **SetupDesign-owned native Expressive
  components**;
- the ColorOS uncheck-mark resource is a **target-verified ColorOS extension**;
- keep the package-local checked/unchecked selector relationship;
- none of these resources should be replaced with Material Symbols.

The source resolver therefore has four public/native tiers:

1. ColorOS native Expressive consumer/resource;
2. AOSP Settings / SettingsLib;
3. AOSP SetupDesign for SUD/Glif components;
4. Google Material Symbols only for remaining generic glyph gaps.

## Current-target divergence from public SetupDesign

Public Android 17 SetupDesign uses:

- checked -> Expressive check-mark glyph;
- unchecked -> no thumb icon.

Current ColorOS 17 uses:

- checked -> Expressive check-mark glyph;
- unchecked -> local Expressive cross glyph.

This is verified target behavior, not a missing upstream icon. It must not be
“normalized” back to AOSP or replaced by a visually similar Material Symbol.
