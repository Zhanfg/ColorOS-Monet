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

Public AOSP-derived SetupDesign source confirms the Expressive switch contract:

- `sud_ic_switch_selector_expressive` is a selector;
- its checked state references `sud_ic_switch_check_mark_expressive`;
- the checked glyph is a 16dp vector tinted with `?attr/colorPrimary`;
- `SwitchItem.updateThumbIconDrawable(...)` installs the selector only while
  checked;
- unchecked state sets the MaterialSwitch thumb icon to `null`.

This matters because the current ColorOS 17 Settings/SystemUI resource tables
also contain:

`sud_ic_switch_uncheck_mark_expressive`

but a public SetupDesign code search does not expose that resource, and the
public SwitchItem path does not require it.

## Project decision

- selector/check resources are treated as **SetupDesign-owned native
  Expressive components**;
- the ColorOS uncheck-mark resource is treated as a **ColorOS extension** until
  a live consumer is proven;
- none of these should be replaced with Material Symbols.

The source resolver therefore now has four public/native tiers:

1. ColorOS native Expressive consumer/resource;
2. AOSP Settings / SettingsLib;
3. AOSP SetupDesign for SUD/Glif components;
4. Google Material Symbols only for remaining generic glyph gaps.
