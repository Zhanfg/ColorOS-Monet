# OPlus Settings homepage icon owner

The full ColorOS 17 Settings APK confirms that the homepage's two-tone icon behavior is not just XML metadata.

## Class ownership

`SettingJumpPreference` extends `COUIJumpPreference` and directly declares:

- `mShowTwoToneColor`
- `mTintIcon`
- `mTintType`
- `mNeedChangeCanvasType`
- `mApplyGlobalTheme`
- normal/warning-color state fields

It also exposes/implements:

- `initAttrs()`
- `onBindViewHolder()`
- `setShowColorTintIcon()`
- `setApplyGlobalTheme()`
- `setTextColor()`

The OPlus homepage row classes inherit this owner:

`SettingsCornerMarkPreference -> SettingsSimpleJumpPreference -> SettingJumpPreference -> COUIJumpPreference`

and:

`SettingsRedDotPreference -> SettingsSimpleJumpPreference -> SettingJumpPreference`.

The airplane-mode row follows the switch branch:

`SettingsAirPlaneSwitchPreference -> SettingSwitchPreference -> COUISwitchPreference`

and declares its own `mShowTwoToneColor` / `mTintType`.

## Combined with XML evidence

`top_level_settings_oplus.xml` has 42 icon-bearing rows:

- 41 opt into `showTwoToneColor=true`;
- 39 request `needChangeDrawType=true`;
- none references a `*_expressive` icon name directly.

This makes the current owner split much clearer:

```text
OPlus homepage XML
  -> OPlus preference subclass
  -> SettingJumpPreference / SettingSwitchPreference
  -> vendor glyph + tint category + two-tone treatment
```

The AOSP SettingsLib Expressive adapter can still own **group geometry**, but homepage icon semantics remain OPlus-owned unless a specific row is proven to use another path.

## Material Symbols implication

Material Symbols must not be bulk-applied to the Settings homepage.

The only acceptable replacement case is a row-specific gap where:

1. the OPlus glyph semantics are understood;
2. the OPlus tint/two-tone contract remains intact or is intentionally replaced at that exact component;
3. an exact native/AOSP Expressive or Material Symbol equivalent exists.

The project should normally keep the existing OPlus glyph and let MD3E influence the surrounding native component, state and semantic color instead.
