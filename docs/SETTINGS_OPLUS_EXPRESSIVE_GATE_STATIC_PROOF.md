# Static proof: ColorOS OPlus homepage and the native Settings Expressive gate

This pass inspects the current PJZ110 ColorOS 17 `Settings.apk` class
definitions and the two trivial OPlus methods directly from DEX.

## 1. OPlus homepage activity does not provide a custom ExpressiveDesignEnabledProvider

Current class:

`com.oplus.settings.feature.homepage.OplusSettingsHomepageActivity`

Superclass:

`androidx.appcompat.app.AppCompatActivity`

Declared interfaces:

none.

Therefore the Android 17
`SettingsThemeHelper.isExpressiveTheme(context)` activity-provider branch does
not receive an OPlus-specific override from this homepage activity.

The relevant native gate remains:

1. SDK;
2. `is_expressive_design_enabled` system property;
3. activity provider only when implemented;
4. exported aconfig flag.

For this OPlus activity, step 3 is absent.

Confidence: HIGH.

## 2. OplusTopLevelSettings really is the AOSP TopLevelSettings subclass

Current class:

`com.oplus.settings.feature.homepage.OplusTopLevelSettings`

Superclass:

`com.android.settings.homepage.TopLevelSettings`

Declared interfaces:

`android.view.View.OnKeyListener`

It does **not** declare an `onCreateAdapter()` override.

Therefore the SettingsLib/SettingsBasePreferenceFragment adapter decision proven
by the Codex report is inherited rather than replaced by an OPlus adapter method.

Confidence: HIGH.

## 3. OPlus style remains intentionally enabled

The current `useOplusStyle()` method is a constant-return method:

```text
const/4 v0, #1
return v0
```

So it returns `true`.

This is important: activating the native Expressive gate is not equivalent to
turning the screen into stock Pixel Settings. The OPlus fragment explicitly
continues to advertise OPlus style.

Confidence: HIGH.

## 4. OPlus XML remains the homepage data source

`getPreferenceScreenResId()` is also a constant-return method and returns:

`0x7f180269 -> xml/top_level_settings_oplus`

Therefore the static composition is:

```text
OplusSettingsHomepageActivity
        ↓
OplusTopLevelSettings
        ↓
top_level_settings_oplus.xml
        +
useOplusStyle() == true
        +
inherited SettingsLib Expressive adapter gate
```

This is a much more precise model than either of these incorrect assumptions:

- "ColorOS simply uses AOSP top_level_settings_expressive.xml"
- "ColorOS completely bypasses the native SettingsLib Expressive path"

Both are false for the analyzed build.

## 5. Practical consequence

The first Settings visual experiment should test the **native gate by itself**
before any custom CardHook/ListHook or wholesale homepage XML replacement.

If the gate produces a coherent UI, the preferred architecture becomes:

- keep OPlus homepage XML;
- keep OPlus preference subclasses and two-tone tint ownership;
- let SettingsLib provide its native Expressive adapter/group treatment;
- optionally bridge only the inner glyph source for the 18 reviewed rows.

The remaining uncertainty is runtime/visual, not static ownership.
