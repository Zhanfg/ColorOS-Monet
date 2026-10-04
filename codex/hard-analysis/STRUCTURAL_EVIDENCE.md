# Structural evidence index

This file records high-signal symbols extracted from the user's ColorOS 17 snapshot. It is intentionally metadata-only.

## UXDesign

DEX:
- classes.dex: 9,552 classes / 65,479 methods
- classes2.dex: 446 classes / 3,494 methods

High-signal types:
- `com.google.ux.material.libmonet.dynamiccolor.TonePolarity`
- `com.google.ux.material.libmonet.dynamiccolor.Variant`
- `com.oplus.materialsdk.uxcolor.color.MaterialStyle`
- `com.oplus.materialsdk.uxcolor.color.utilities.Variant`
- `com.oplus.uxdesign.personal.uxcolor.UxColorThemeController`
- `com.oplus.uxdesign.personal.uxcolor.UxVectorDrawableController`
- `com.oplus.uxdesign.uxcolor.UxColorApplication`
- `com.oplus.uxdesign.uxcolor.UxColorPalettePanel`
- `com.oplus.uxdesign.uxcolor.UxColorSettingActivity`
- `com.oplus.uxdesign.uxcolor.UxColorSettingProvider`
- `com.oplus.uxdesign.uxcolor.UxWallpaperColorSettingActivity`
- `com.oplus.uxdesign.uxcolor.UxWallpaperColorSettingFragment`
- `com.oplus.uxdesign.uxcolor.autocheck.UxColorAutoCheckManager`
- `com.oplus.uxdesign.uxcolor.autocheck.UxColorUpdateManager`
- `com.oplus.uxdesign.uxcolor.bean.UxColorManager`
- `com.oplus.uxdesign.uxcolor.bean.UxWallpaperColor`

Observed central signatures:
- `a8/b.a(MaterialStyle utilities object, boolean)`
- `a8/b.b(MaterialStyle, boolean, Context, ...)`
- `a8/b.e(Context, int, boolean, MaterialStyle)`

## Settings / COUI

High-signal types:
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

Observed strings include:
- `COUICustomListSelectedLinearLayout_couiPreferenceWithDividerItem`
- multiple COUI divider/list/card attributes
- homepage configuration flags.

## SystemUI

Observed dynamic-color types:
- `com.android.systemui.monet.CustomDynamicColors`
- `com.android.systemui.monet.DynamicColors`
- `com.android.systemui.monet.SchemeClock`
- `com.android.systemui.monet.SchemeClockVibrant`
- `com.google.ux.material.libmonet.dynamiccolor.MaterialDynamicColors`
- `com.oplus.materialsdk.uxcolor.m3color.DynamicColorsOptions`
- `com.oplus.materialsdk.uxcolor.m3color.m3.UxMaterialDynamicColors`
- `com.oplus.materialsdk.uxcolor.m3color.m3.OriginalAlgorithm.MaterialDynamicColors`

Observed component types:
- `com.oplus.systemui.qs.widget.SimpleQsClock`
- `com.oplus.systemui.volume.OplusVolumeDialogImpl`

SystemUIPlugin:
- `com.oplus.systemui.plugins.shared.template.section.media.MediaPlayerCardPageRootView`

## COE 2.9.3

DEX:
- 3,935 classes / 22,433 methods.

High-signal hooks:
- `one.dot.couiexpressive.hooks.widget.CardHook`
- `one.dot.couiexpressive.hooks.widget.ListHook`
- `one.dot.couiexpressive.hooks.systemui.MonetColorSpec2025Hook`
- `one.dot.couiexpressive.hooks.systemui.QsLottieHook`
- `one.dot.couiexpressive.hooks.systemui.AospMediaCardHook`

The handoff should treat these identifiers as starting points, not as proof of runtime ownership.
