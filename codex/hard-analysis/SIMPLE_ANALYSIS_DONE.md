# Simple analysis already completed — do not spend Codex time here

These items are intentionally kept out of the hard-analysis queue.

## Legacy overlay classifier

The old v0.1.4 resource-only payload was classified against the current ColorOS 17 target dump:

- 32 legacy overlay APKs
- 2,938 resource entries
- 834 → restore native
- 613 → preserve target artwork/geometry; tint only when justified
- 385 → drop removed resource
- 285 → migrate renamed or drop
- 49 initial high-confidence semantic accents
- remaining ambiguous/content resources require component-level decisions

The shipping direction is already documented in
`docs/COLOROS17_LEGACY_RESOURCE_CLASSIFICATION.md`.

## OEM RROs

### SettingsResCommon_Sys.apk
- package: `com.android.settings.overlay.common`
- target: `com.android.settings`
- static, priority 0
- only color-mode option arrays, network-scan timeout and related strings in this build.
- It is **not** the source of the grouped-card geometry problem.

### SystemUIResCommon_Sys.apk
- package: `com.android.systemui.overlay.common`
- target: `com.android.systemui`
- static, priority 0
- only `config_quickSettingsAutoAdd`, `doze_display_state_supported`, `pixel_pitch`.
- It is **not** the owner of QS card geometry.

### OplusSystemuiResOverlay.apk
- package: `com.android.systemui.oplus.res.overlay`
- target: `com.android.systemui`
- static, priority 100
- Wi-Fi signal drawables, fingerprint background, AOD default style/repeat count.
- Treat as a narrow OEM feature RRO, not the global MD3E surface layer.

### com.android.SystemUIResOverlay.23821.apk
- target: `com.android.systemui`
- static, priority 700
- this device variant mainly supplies three-key hardware/UI resources and dimensions.
- Not the main QS/notification/volume design owner.

## Navigation overlays

- `TransparentNavigationBarOverlay`: dynamic overlay on `android`; enables transparent nav bar.
- `NavigationBarMode3ButtonOverlay`: dynamic interaction-mode overlay.
- `NavigationBarModeGesturalOverlay`: dynamic interaction-mode overlay; controls gesture/nav frame dimensions and gesture inset.
- `PUIThemedHandleBarDimen`: static SystemUI RRO; zeros handle dimensions for its themed mode.

These are component-specific and should not be folded into generic Settings/SystemUI card logic.

## Existing architecture decisions

- Native-foundation correction RROs are migration/debug only; clean v0.2.0 should not need them after old global overlays are removed.
- Generic vendor-icon redraws are retired.
- ColorOS native EXPRESSIVE palette is optional and disabled by default.
- v0.2.0 shipping scope is ColorOS/system-only; X/TIM/Coolapk are excluded.
