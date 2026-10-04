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
- `SwitchItem` references the Expressive selector under the Glif Expressive
  activation path.

The verifier intentionally does **not** assert a specific public unchecked
runtime branch unless that behavior is directly proven from the pinned source.

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

Public Android 17 SetupDesign proves the checked Expressive selector/check
family and its Glif Expressive activation path.

Current ColorOS 17 additionally proves, in the target resource XML:

- checked -> Expressive check-mark glyph;
- unchecked -> local Expressive cross glyph.

This is verified target behavior, not a missing upstream icon. It must not be
“normalized” back to AOSP or replaced by a visually similar Material Symbol.


## Official verifier result

Pinned Android 17 SetupDesign verification confirms all three resource files
exist at the release commit:

- `sud_ic_switch_selector_expressive.xml`
- `sud_ic_switch_check_mark_expressive.xml`
- `sud_ic_switch_uncheck_mark_expressive.xml`

The verifier deliberately does not infer the active unchecked runtime path from
resource existence alone. Component code/theme state remains the behavioral
owner.
