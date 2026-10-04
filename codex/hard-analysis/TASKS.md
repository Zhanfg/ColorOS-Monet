# Hard-analysis task list

## Task A — UXDesign / native Monet / EXPRESSIVE

Primary source snapshot:
- `UXDesign.apk` SHA-256 `324080bc89384e12bff294ccbbffad19249cd2cfd6e8b70b7eea61e1c726d137`
- 2 DEX files, ~9,998 classes / ~68,973 methods total.

Known high-signal symbols:
- `com.google.ux.material.libmonet.dynamiccolor.*`
- `com.oplus.materialsdk.uxcolor.color.MaterialStyle`
- `com.oplus.materialsdk.uxcolor.color.utilities.Variant`
- `com.oplus.uxdesign.personal.uxcolor.UxColorThemeController`
- `com.oplus.uxdesign.uxcolor.UxColorSettingActivity`
- `com.oplus.uxdesign.uxcolor.UxWallpaperColorSettingActivity`
- `com.oplus.uxdesign.uxcolor.UxWallpaperColorSettingFragment`
- `com.oplus.uxdesign.uxcolor.UxColorSettingProvider`
- `com.oplus.uxdesign.uxcolor.bean.UxColorManager`
- central obfuscated methods seen around `a8/b::{a,b,e}` taking `MaterialStyle`.

Known runtime strings:
- `/data/oplus/uxres/uxcolor`
- `/data/oplus/uxres/uxcolor/temp/coui_theme_color_online.xml`
- `/data/oplus/uxres/uxcolor/temp/coui_theme_color_night_online.xml`
- `theme_customization_overlay_packages`
- variants include `TONAL_SPOT`, `EXPRESSIVE`, `VIBRANT`, etc.

Questions to answer:
1. Exact flow from WallpaperColors/seed → style/variant → palette generation → persisted/generated resources.
2. Exact mapping between Android theme-style strings and OPlus `MaterialStyle` / libmonet `Variant`.
3. Whether UXDesign writes FRRO/RRO, XML, Settings.Secure, or multiple layers; identify the owner of each step.
4. Which public/runtime color resources Settings/SystemUI consume after UXDesign updates.
5. Whether changing only `android.theme.customization.theme_style` is sufficient, incomplete, or unsafe.
6. Best integration point for our module that respects later user theme changes.

Deliver `reports/01_UXDESIGN_MONET_PIPELINE.md`.

## Task B — Settings / COUI grouped cards

Known ColorOS 17 classes:
- `com.android.settings.homepage.SettingsHomepageActivity`
- `com.android.settings.homepage.TopLevelSettings`
- `com.coui.appcompat.cardlist.COUICardListHelper`
- `com.coui.appcompat.cardlist.COUICardListSelectedItemLayout`
- `com.coui.appcompat.list.IListSelectedItem`
- `com.coui.appcompat.list.ICardListSelectedItem`
- `com.coui.appcompat.preference.ListSelectedItemLayout`
- `com.coui.appcompat.preference.COUICardSupportInterface`
- `com.coui.appcompat.preference.COUICustomListSelectedLinearLayout`
- `com.coui.appcompat.toolbar.AppBarBlurHelper`
- `com.coui.appcompat.toolbar.ToolbarMaterialEffectDelegate`
- `com.oplus.settings.feature.deviceinfo.aboutphone.OplusHighlightablePreferenceGroupAdapter`
- `com.oplus.settings.feature.deviceinfo.aboutphone.DeviceInfoFragment`

Known ColorOS 17 strings/attrs include divider/list-card concepts such as
`COUICustomListSelectedLinearLayout_couiPreferenceWithDividerItem`.

Questions:
1. How ordinary preference groups are assembled: group container vs first/middle/last/single item.
2. Which class decides card position/shape and which class draws dividers.
3. Exact field/method replacement for the ColorOS 16-era `mCardBackgroundColor` assumptions.
4. Why the old COE CardHook/ListHook makes all pages look like separate small cards on ColorOS 17.
5. Separate policies for Settings homepage, normal secondary pages, About Device, dialogs/popups.
6. Produce a **screen/component whitelist** for future segmented-card behavior. No package-wide rule.

Deliver `reports/02_SETTINGS_GROUPED_CARD_MODEL.md`.

## Task C — SystemUI + SystemUIPlugin

Known ColorOS 17 symbols:
- `com.android.systemui.monet.DynamicColors`
- `com.android.systemui.monet.CustomDynamicColors`
- `com.android.systemui.monet.SchemeClock`
- `com.android.systemui.monet.SchemeClockVibrant`
- `com.google.ux.material.libmonet.dynamiccolor.MaterialDynamicColors`
- `com.oplus.materialsdk.uxcolor.m3color.DynamicColorsOptions`
- `com.oplus.materialsdk.uxcolor.m3color.m3.UxMaterialDynamicColors`
- `com.oplus.systemui.qs.widget.SimpleQsClock`
- `com.oplus.systemui.volume.OplusVolumeDialogImpl`
- SystemUIPlugin: `com.oplus.systemui.plugins.shared.template.section.media.MediaPlayerCardPageRootView`

Questions:
1. Map ownership of QS tile color/shape/icon animation/Lottie between base SystemUI and plugin.
2. Map notification, media and volume component roots and their color/shape/blur providers.
3. Find the real dynamic-color path used by each component; avoid assuming one global SystemUI palette.
4. Identify blur/translucency APIs and which resources are just fallback values.
5. Identify motion/ripple/shape entry points suitable for MD3E without replacing native component architecture.
6. Produce separate hook contracts for QS, notification, media, volume, clock.

Deliver `reports/03_SYSTEMUI_COMPONENT_MAP.md`.

## Task D — COE 2.9.3 migration

Source APK SHA-256:
`45cf72d7e872cc11433a5e67a1e3755bac7f779263ef8df511deaec17376e7b7`

Known hooks:
- `one.dot.couiexpressive.hooks.widget.CardHook`
- `one.dot.couiexpressive.hooks.widget.ListHook`
- `one.dot.couiexpressive.hooks.systemui.MonetColorSpec2025Hook`
- `one.dot.couiexpressive.hooks.systemui.QsLottieHook`
- `one.dot.couiexpressive.hooks.systemui.AospMediaCardHook`

Observed ColorOS 17 failure:
- repeated `NoSuchFieldError` for `mCardBackgroundColor` in
  - `COUICustomListSelectedLinearLayout`
  - `COUICardListSelectedItemLayout`

Known target migrations already observed:
- `SimpleQSClock` → `SimpleQsClock`
- old media root → `...template.section.media.MediaPlayerCardPageRootView`
- `com.android.systemui.volume.VolumeDialogImpl` is not the OPlus owner; `OplusVolumeDialogImpl` remains.
- old assumptions around `com.android.systemui.monet.Style` are invalid; newer DynamicColors/Scheme classes exist.

Questions:
1. Build an old-hook → ColorOS17-target compatibility matrix.
2. For every failed hook, state: keep / retarget / replace / delete.
3. Replace package-wide CardHook/ListHook with component/screen predicates.
4. Verify MonetColorSpec2025Hook against the actual ColorOS 17 UXDesign/SystemUI color pipeline.
5. Verify QsLottieHook against the new QS icon path.
6. Give the minimum source-level patch plan; do not recommend binary no-op patching as the final architecture.

Deliver `reports/04_COE_293_ANDROID17_MIGRATION.md`.
