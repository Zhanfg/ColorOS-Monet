# ColorOS 17 Settings homepage routing

The static Settings evidence is now strong enough to separate two different
things that were previously easy to conflate:

1. AOSP/SettingsLib has a native Expressive homepage path.
2. The ColorOS launcher entry actually routes through an OPlus homepage
   activity/fragment override.

## Manifest route

The current ColorOS 17 Settings manifest declares:

- `android.settings.SETTINGS` on
  `com.oplus.settings.feature.homepage.OplusSettingsHomepageActivity`.
- launcher alias `com.android.settings.Settings` targets the same OPlus
  homepage activity.

Therefore the real ColorOS Settings home is not merely the stock
`SettingsHomepageActivity` path.

## Fragment route

Static DEX evidence shows:

`OplusSettingsHomepageActivity`
→ `BaseHomePageImpl.getSwitchDefaultFragment()`
→ `new OplusTopLevelSettings()`

and:

`OplusTopLevelSettings extends TopLevelSettings`.

This matters because `OplusTopLevelSettings` overrides
`getPreferenceScreenResId()`.

## Exact resource IDs

The current resource table resolves:

- `0x7f180265` → `xml/top_level_settings`
- `0x7f180266` → `xml/top_level_settings_expressive`
- `0x7f180267` → `xml/top_level_settings_expressive_desktop`
- `0x7f180268` → `xml/top_level_settings_no_merge`
- `0x7f180269` → `xml/top_level_settings_oplus`

AOSP `TopLevelSettings.getPreferenceLayoutResId(Context)` selects among the
first three paths, including the native Expressive XML.

ColorOS `OplusTopLevelSettings.getPreferenceScreenResId()` returns
`0x7f180269` unconditionally in the analyzed build.

## Consequence

The existence of `top_level_settings_expressive.xml` and
`ic_settings_*_expressive` does **not** prove that the current ColorOS
homepage actually consumes them.

The decisive OPlus homepage XML has now been decoded from the user's current
Settings APK. It contains 42 icon-bearing rows and preserves explicit OPlus
preference classes, controllers, two-tone tint types and layout categories.

The exact row inventory is recorded in
`compat/coloros17/settings_oplus_homepage_icons.tsv`, and the complete source
decision is recorded in
`compat/material-symbols/settings_homepage_full_source_map.tsv`.

Therefore the remaining icon question is no longer resource ownership. It is
visual/runtime verification of the selected glyph source inside the existing
OPlus two-tone/container pipeline.

Policy:

- do not force the AOSP Expressive homepage XML;
- keep the native OPlus homepage structure and tint owner;
- prefer native Expressive glyphs where exact;
- use Material Symbols only for generic rows with an exact semantic match;
- keep OEM/service-specific rows native.

## Why this is useful

This closes the resource-ID ambiguity from the Codex report and turns the
remaining homepage question into a narrow XML consumer check instead of another
full Settings reverse-engineering pass.

Machine-readable evidence:

- `compat/coloros17/settings_expressive_gate.tsv`
- `compat/coloros17/settings_homepage_route.tsv`
