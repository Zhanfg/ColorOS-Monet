# ColorOS 17 Settings resource-XML evidence

Source: user's PJZ110 ColorOS 17 `Settings.apk` from the frozen audit snapshot.

This document records **derived structure only**. Vendor XML/path payloads are not committed.

## 1. Homepage theme is COUI-native, not SettingsLib Expressive

The manifest binds:

`com.oplus.settings.feature.homepage.OplusSettingsHomepageActivity`

to:

`Theme.Settings.Home.Oplus`

The resolved style chain is:

```text
Theme.Settings.Home.Oplus
  -> AppBaseTheme.NoActionBar.Settings
  -> preferenceTheme = AppBaseTheme.Homepage

AppBaseTheme.Homepage
  -> PreferenceThemeOverlay.COUITheme
  -> CardPreference
  -> OplusSettingsPreferenceFragmentCompatStyle.NoDivider
  -> Preference.COUI.SwitchPreference
```

Therefore the current ColorOS homepage is not simply using
`PreferenceTheme.SettingsLib.Expressive`.

**Decision:** do not replace the homepage preference theme globally with the
AOSP/SettingsLib Expressive theme.

Confidence: HIGH.

## 2. SettingsLib Expressive is a separate v36 theme family

The current APK also contains:

`Theme.SettingsBase.Expressive`

which resolves to:

`PreferenceTheme.SettingsLib.Expressive`

That preference theme switches individual preference types to explicit
Expressive layouts, including:

- `settingslib_expressive_preference`
- `settingslib_expressive_preference_category`
- `settingslib_expressive_preference_dropdown`
- `settingslib_expressive_preference_switch`
- `settingslib_expressive_preference_two_target`

This is real Expressive infrastructure, but it is a **separate theme family**,
not proof that the OPlus homepage currently opts into it.

Confidence: HIGH.

## 3. Native COUI grouped cards are continuous groups

The current ColorOS preference row layout uses:

`com.coui.appcompat.preference.COUICustomListSelectedLinearLayout`

The legacy/native COUI card background family is split into:

- head
- body
- foot
- full

with horizontal inset `16dp`, card radius `12dp`, and
`coui_color_card_background`.

The head drawable rounds only the top corners, the body has no outer corner
rounding, the foot rounds only the bottom corners, and full rounds all corners.

This exactly matches the Codex static conclusion that ordinary ColorOS Settings
groups are rendered as a continuous group using first/middle/last/single state.

Confidence: HIGH.

## 4. SettingsLib Expressive card geometry is different

`settingslib_expressive_card_background` resolves to a shape with:

- surface role: `settingslib_materialColorSurfaceBright`
- radius: **28dp**

This is not the same geometry family as the native COUI 12dp grouped rows.

Therefore applying the SettingsLib Expressive card background to every COUI row
would visually split native groups and reproduce the “many independent small
cards” failure mode.

Confidence: HIGH.

## 5. Expressive segmented button is a component, not a row-group policy

The APK contains:

`settingslib_expressive_preference_segmentedbutton`

Its root contains a `MaterialButtonToggleGroup` with single selection and
selection required.

That resource is evidence for an Expressive **segmented-control preference
component**. It is not evidence that ordinary Settings rows should become
segmented cards.

Confidence: HIGH.

## 6. Implementation consequence

The Settings policy is now:

```text
ordinary ColorOS preference group
    -> KEEP native COUI first/middle/last/single grouping

verified SettingsLib Expressive component
    -> may reuse its native Expressive layout/theme

new segmented-card behavior
    -> only after exact Activity + Fragment + Adapter + preference key
       + View + layout/role tuple is proven
```

The segmented-card whitelist therefore remains empty until runtime/consumer
evidence closes the tuple.

## 7. Remaining evidence

Still required before enabling a segmented-card hook:

- exact consumer for each candidate Expressive layout;
- Activity/Fragment/adapter/preference-key tuple;
- runtime confirmation that the expected theme/layout is active;
- fault provenance for the historical `NoSuchFieldError`.

The XML evidence closes the **resource-structure** gap, not the runtime-binding
gap.
