# ColorOS 17 compatibility notes

Probe baseline:

- Device: PJZ110
- Build: `PJZ110_17.0.0.101(SP02CN01)`
- Android: 17 / SDK 37
- Settings: 17.0.0
- SystemUI: 17.99.02
- Launcher: 17.3.9
- NotificationCenter: 17.100.012
- WirelessSettings: 17.5.16
- SystemUIPlugin: 17.000.002
- COE: 2.9.3.261003

## RRO findings

`cmd overlay list` and `cmd overlay lookup` return
`Failed transaction (2147483646)` even when scoped to one target/resource on
this firmware. Therefore the earlier hypothesis that the failure was caused
only by an oversized unscoped overlay listing is not supported.

`idmap2 dump`, however, works and proves that the mounted legacy overlays are
being compiled into idmaps. Observed mapping counts:

| Legacy overlay | mapped | missing |
| --- | ---: | ---: |
| Setting.apk | 199 | 38 |
| SystemUI_dual_monet.apk | 366 | 76 |
| Launcher.apk | 95 | 32 |
| Notificationmanager.apk | 42 | 26 |
| Wirelesssetting.apk | 79 | 26 |

The old Settings overlay still maps resources such as
`settings_about_device_ic` and `settings_device_name_ic`, but it has no
entries for the new ColorOS 17 About-device card resources:

- `device_market_name_phone_icon`
- `ic_device_cpu_card`
- `ic_device_spec_card_placeholder`
- `ic_device_info_camera_decor`
- `ic_device_battery_trailing`
- `ic_device_screen_info_card`
- `ic_device_security_chip_card`
- `ic_tidal_architecture_card`

The `coloros-settings17` overlay is a narrow, independently authored
compatibility layer for exactly these resources. It is packaged as a separate
systemless hotfix so it can be tested without replacing the existing 32-overlay
module.

## COE / SystemUI class migration

A string-level FQCN audit of COE 2.9.3 found 224 SystemUI/OPlus class
references. On this build, 180 are present in `SystemUI.apk`; six additional
media template classes are present in `SystemUIPlugin.apk`; 38 referenced
classes are absent from both.

Confirmed migration clues include:

- `com.oplus.systemui.common.helper.SystemTypefaceHelper`
  -> `com.oplusos.systemui.common.typeface.SystemTypefaceHelper`
- `com.oplus.systemui.qs.widget.SimpleQSClock`
  -> `com.oplus.systemui.qs.widget.SimpleQsClock`
- `com.oplus.systemui.plugins.shared.view.template.media.MediaPlayerCardPageRootView`
  -> `com.oplus.systemui.plugins.shared.template.section.media.MediaPlayerCardPageRootView`
- `com.android.systemui.volume.CsdWarningDialog`
  -> `com.android.systemui.volume.CsdWarningDialogDelegate`
- AOSP `com.android.systemui.volume.VolumeDialogImpl` is absent while
  `com.oplus.systemui.volume.OplusVolumeDialogImpl` remains.
- `com.android.systemui.monet.Style` is absent. `ColorScheme`,
  `DynamicColors`, `CustomDynamicColors`, `SchemeClock`, `SchemeClockVibrant`,
  `Shades`, and `TonalPalette` are present.

These findings are compatibility identifiers only; no target APK, bytecode, or
vendor artwork is committed.
