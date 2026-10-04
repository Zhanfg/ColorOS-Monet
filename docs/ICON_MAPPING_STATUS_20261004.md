# Icon mapping status — 2026-10-04

Pinned sources:

- Google Material Symbols: `google/material-design-icons@737e3324305806514d7909874fa1818ae1808232`
- AOSP Settings stable reference: `android-17.0.0_r1@213829fb67f5e070029e0513a088f31bc8f5c1ed`
- ColorOS target: current PJZ110 ColorOS 17 snapshot supplied by the user.

## Proven upstream inventory

The pinned Material Symbols Android tree contains **4,150 symbol directories**.

Current curated ColorOS mapping references **57 unique Material Symbols**. CI verifies every requested 24px Rounded VectorDrawable directly through the GitHub API at the pinned commit. Current verification is green.

## ColorOS native Expressive inventory

The current target dump exposes **133 drawable/mipmap entries containing `expressive`**.

After excluding generated animation-frame internals:

- **36** direct base -> native Expressive sibling pairs are mechanically proven.
- **73** named Expressive resources remain without a trivial same-package sibling and require consumer/AOSP analysis.

Examples of proven siblings:

- `ic_help -> ic_help_expressive`
- `ic_notifications -> ic_notifications_expressive`
- `ic_settings_display -> ic_settings_display_expressive`
- `ic_settings_security -> ic_settings_security_expressive`
- `ic_settings_wireless -> ic_settings_wireless_expressive`
- `ic_storage -> ic_storage_expressive`
- `settingslib_card_background -> settingslib_expressive_card_background`

## AOSP Settings wrapper evidence

Public AOSP Settings Expressive work shows that many homepage Expressive drawables are wrappers around existing filled glyphs plus category-specific tint roles, rather than a separate glyph set.

The project records 16 high-signal wrapper mappings in
`aosp_settings_expressive_wrappers.tsv`.

This strongly supports the project order:

`native filled geometry -> native/AOSP Expressive wrapper -> semantic tint`

before considering an imported Material Symbol.

## Current source-resolution table

The validated CI resolver currently produces **105 reviewed-source rows**:

- **36** `COLOROS_NATIVE_EXPRESSIVE`
- **10** `COLOROS_NATIVE_EXPRESSIVE_CANDIDATE`
- **59** `GOOGLE_MATERIAL_SYMBOL_CANDIDATE`

All 105 remain behind `PENDING_CONSUMER_TRACE`. No icon replacement is shipped automatically.

Four Material Symbol candidates were explicitly demoted because an exact native Expressive sibling already exists:

- Settings `ic_help`
- Settings `ic_storage`
- Settings `ic_notifications`
- Settings `ic_settings_security`

## Full generic inventory

The current ColorOS 17 inventory contains **1,805** resources classified as generic icon candidates.

With the state-preserving name matcher and the pinned 4,150-symbol catalog, **180** currently have a deterministic name-level Material Symbol match:

- 106 exact core-name matches
- 21 size-suffix removals
- 25 presentation-suffix removals
- 28 state-suffix fallbacks

These 180 are only candidate generation. They are not shipping mappings until the real consumer is known.

## Shipping gate

An icon may ship only after:

1. the real target consumer is identified;
2. native Expressive resources are checked first;
3. AOSP Expressive integration is checked second;
4. Material Symbols is used only as the exact generic fallback;
5. size/state/tint behavior is explicitly defined;
6. the mapping is promoted out of `NEEDS_REVIEW`.

This keeps the icon migration native-first and auditable.


## OPlus homepage consumer closure

The real `top_level_settings_oplus.xml` has now been inspected from the current
ColorOS 17 Settings APK.

- 42 homepage rows have explicit icon resources;
- 41/42 opt into OPlus two-tone icon handling;
- 39/42 request OPlus draw-type conversion;
- none of the 42 resources directly uses a `*_expressive` icon name.

DEX class structure independently confirms that
`SettingJumpPreference` owns the two-tone/tint fields used by the row
subclasses.

Therefore the AOSP-style `ic_settings_*_expressive` family is **not** treated
as the ColorOS homepage source. Those resources remain valid for their real
non-homepage consumers, while the OPlus homepage keeps its own icon pipeline.
