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

For the main ColorOS Settings homepage, the next decisive artifact is:

`res/xml/top_level_settings_oplus.xml`

We need to inspect its preference/icon references and any OPlus controller-side
rebinding before promoting homepage icon replacements.

Until then:

- do not force the AOSP Expressive homepage XML;
- do not replace homepage icons with Material Symbols;
- keep the native ColorOS home structure;
- use the AOSP/Material assets as reference/fallback only.

## Why this is useful

This closes the resource-ID ambiguity from the Codex report and turns the
remaining homepage question into a narrow XML consumer check instead of another
full Settings reverse-engineering pass.

Machine-readable evidence:

- `compat/coloros17/settings_expressive_gate.tsv`
- `compat/coloros17/settings_homepage_route.tsv`
