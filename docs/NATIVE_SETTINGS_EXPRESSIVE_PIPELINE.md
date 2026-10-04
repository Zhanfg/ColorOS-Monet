# Native Settings Expressive pipeline on ColorOS 17

The project no longer needs to recreate Settings segmented/grouped cards with a package-wide COE hook.

The current ColorOS 17 Settings APK already contains the Android 17 SettingsLib Expressive implementation, and the current DEX keeps the same high-value control points as public AOSP.

## Native gate

`SettingsThemeHelper.isExpressiveTheme(context)` follows this order:

1. require SDK >= 36;
2. read `SystemProperties.getBoolean("is_expressive_design_enabled", false)`;
3. if true, return true immediately;
4. otherwise, if the current Activity implements `ExpressiveDesignEnabledProvider`, ask the Activity;
5. otherwise return the AConfig-backed `Flags.isExpressiveDesignEnabled()`.

The AConfig implementation reads package `com.android.settingslib.widget.theme.flags`, flag `is_expressive_design_enabled`, default false.

## Native preference grouping

When the gate is true, `SettingsBasePreferenceFragment.onCreateAdapter()` returns `SettingsPreferenceGroupAdapter`.

The native adapter computes real section states `state_first`, `state_middle`, `state_last`, and `state_single` using preference parents, expanded groups and explicit group-divider preferences. `updateBackground()` then applies the corresponding stateful rounded background while preserving icon-space and section padding semantics.

This supersedes the old package-wide COE CardHook/ListHook model.

## Divider and spacing behavior

`SettingsBasePreferenceFragment.onViewCreated()` removes the legacy RecyclerView divider only inside the native Expressive path and adds the SettingsLib margin decoration when spacing is enabled. This is component-scoped behavior, not a global COUI divider override.

## ColorOS homepage remains OPlus-owned

The actual route is:

`OplusSettingsHomepageActivity -> BaseHomePageImpl.getSwitchDefaultFragment() -> new OplusTopLevelSettings()`.

`OplusTopLevelSettings` uses `xml/top_level_settings_oplus`, but its inheritance chain still reaches `SettingsBasePreferenceFragment`. Therefore the native Expressive adapter path can apply without replacing the OPlus homepage XML.

The exact OPlus XML preference keys/layout references remain a validation gate.

## Homepage icons

`DashboardFeatureProviderImpl.setPreferenceIcon()` checks the same Expressive gate. When active, `getExpressiveHomepageIcon()` keeps the real tile glyph, normalizes its size, selects the category color scheme, tints the foreground, and wraps it in the native rounded AdaptiveIcon background.

So the preferred Settings icon model is usually:

`existing semantic glyph -> native Expressive container/color treatment`

not wholesale Material Symbol replacement.

## Architecture decision

```text
ColorOS OPlus Settings structure/XML
        ↓
native SettingsThemeHelper Expressive gate
        ↓
native SettingsPreferenceGroupAdapter
        ↓
native first/middle/last/single backgrounds + spacing
        ↓
native DashboardFeatureProvider Expressive icon treatment
        ↓
small semantic Monet tint layer only where still needed
```

Do not ship package-wide CardHook/ListHook, global COUI divider/radius replacement, or Settings-home Material Symbol replacement while the native pipeline already owns the component.

## Validation status

Static confidence is HIGH. Shipping remains gated on a device experiment because OPlus preference XML and vendor subclasses can still alter final rendering.

The reversible no-reboot probe is `experiments/ColorOS17_NativeSettingsExpressive_Probe.sh`. It changes only the dedicated native debug-override property and never changes the user's Monet/theme style.
