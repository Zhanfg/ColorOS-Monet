# ColorOS 17 Native-First + MD3E baseline

Source snapshot: PJZ110 / Android 17 / ColorOS 17 V17.0.0, build PJZ110_17.0.0.101(SP02CN01), collected 2026-10-03.

## Runtime baseline

- Resolution: 1440x3168
- Density: 640 dpi
- Font scale: 1.0
- Window / transition animation scale: 1.0
- `persist.sys.oplus.material_blur_switch=true`
- SurfaceFlinger background blur is supported and media panel blur is enabled.
- Dynamic color source is home wallpaper.
- Current Google theme style is `TONAL_SPOT`.
- `material_you_overlay_enable=1`.

## Important discovery: ColorOS 17 already contains its own Monet / Expressive infrastructure

`com.oplus.uxdesign` is version 17.0.15 and targets SDK 37.

Its DEX includes:

- `com.google.ux.material.libmonet.dynamiccolor.*`
- OPlus `uxcolor/monet/Style`
- `EXPRESSIVE`
- `GOOGLE_COLOR_EXPRESSIVE_STYLE_INDEX`
- `TONAL_SPOT`
- `DynamicColorsOptions`
- `material_you_overlay_enable`
- `wallpaper_color_overlay_enable`
- `theme_customization_overlay_packages`
- `UxWallpaperColorSettingActivity`

Therefore v0.2.0 must integrate with ColorOS' existing dynamic-color pipeline instead of replacing it with an independent palette engine.

## OEM RROs confirmed in the current ROM

The final visual stack includes, among others:

- SettingsResCommon_Sys.apk
- SystemUIResCommon_Sys.apk
- OplusSystemuiResOverlay.apk
- com.android.SystemUIResOverlay.23821.apk
- NavigationBarModeGesturalOverlay.apk
- NavigationBarMode3ButtonOverlay.apk
- TransparentNavigationBarOverlay.apk
- PUIThemedHandleBarDimen.apk
- OplusPermissionControllerOverlay.apk

Implementation must resolve these layers before applying module overrides.

## UI infrastructure confirmed

Current ROM contains:

- UXDesign.apk
- SettingsIntelligence.apk
- OppoPackageInstaller.apk
- DocumentsUI.apk
- IntentResolver.apk
- AccessibilityMenu.apk
- Theme Store 17.11.17
- WallpaperChooser / Wallpapers
- game_settings.apk
- oplus-framework.jar / oplus-services.jar / oplus-framework-res.apk

This is sufficient for the first system-wide visual architecture pass.

## Native-first design rule

v0.2.0 must preserve:

1. ColorOS blur and translucency where already implemented well.
2. Native grouped-list structure and divider semantics.
3. Native component geometry where it encodes hierarchy.
4. Native icon geometry and alpha structure.
5. Existing theme/wallpaper dynamic-color source.
6. OEM navigation/system UI dimensional overlays.

MD3E is added only where it improves semantic hierarchy, state communication, motion or dynamic color.

## P0 migration rules

- Do not globally zero `coui_list_divider_height`.
- Do not globally make `coui_color_divider` transparent.
- Do not globally replace `coui_round_corner_*` to force one card style.
- Do not run segmented-card behavior package-wide.
- Ordinary Settings preference groups remain continuous grouped lists.
- Segmented cards are component-scoped and must know first/middle/last item position.
- Popup/menu/dialog geometry uses its own component family.
- SystemUI QS / notification / media / volume geometry is independent from Settings geometry.

## Dynamic color rule

Use the ColorOS/Android active Monet source and map semantic roles instead of flattening many OEM colors onto a single surface token.

Required distinct roles:

- page background
- grouped container
- elevated container
- active/selected container
- state layer
- divider/outline
- primary/secondary content
- accent roles

## Versioning

This is a design-system reconstruction and belongs to the v0.2.0 line, not another v0.1.5 hotfix.
