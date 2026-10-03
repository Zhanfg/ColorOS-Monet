# ColorOS 17 legacy overlay audit — 2026-10-03 baseline

This is an aggregate clean-room compatibility report generated from the user's local ColorOS 17 target dump and the legacy v0.1.4 resource-only overlay set. No vendor APK, artwork, path data or proprietary resource payload is committed here.

## Coverage

- Legacy overlay APKs examined: **32**
- Legacy resource entries examined: **2,938**
- Overlay instances whose ColorOS 17 target package was captured: **31 / 32**
- The only absent legacy target package is `com.oneplus.oshare`; the current ROM exposes the ColorOS OShare package instead.

## Classification result

| Decision | Count | Meaning |
|---|---:|---|
| `RESTORE_NATIVE` | **834** | Shared geometry, neutral surfaces, state, motion, etc. should be owned by ColorOS 17 |
| `REVIEW` | **659** | Ambiguous resource; no global rewrite is justified |
| `PRESERVE_TARGET_GEOMETRY_TINT_ONLY` | **613** | Keep ColorOS 17 icon geometry; tint only when semantically appropriate |
| `DROP_REMOVED_RESOURCE` | **385** | Legacy resource no longer exists in the current target |
| `MIGRATE_RENAMED_OR_DROP` | **285** | Resource family appears obsolete/renamed and requires an explicit migration |
| `MD3E_SEMANTIC` | **102** | Strong candidate for native Monet/MD3E semantic color mapping |
| `MD3E_CONTENT_OR_NATIVE` | **60** | Content color needs component-level judgment |

## Important package results

- Settings: **237** legacy entries; **199** still exist and **38** are removed/renamed.
- Launcher: **127** legacy entries; **95** still exist and **32** are removed/renamed.
- WirelessSettings: **105** legacy entries; **79** still exist and **26** are removed/renamed.
- NotificationManager: **68** legacy entries; **42** still exist and **26** are removed/renamed.
- SystemUI dual Monet: **442** legacy entries; **366** still exist and **76** are removed/renamed.
- SystemUI single Monet: **442** legacy entries; **366** still exist and **76** are removed/renamed.

These counts independently reproduce the earlier idmap-oriented migration picture and explain why a global legacy-overlay reuse strategy cannot be considered Android 17 complete.

## Architecture consequence

v0.2.0 must stop treating the legacy overlay payload as the design system.

The intended ownership model is:

1. **ColorOS 17 owns** geometry, dividers, blur/translucency, neutral surfaces, default state layers, typography metrics and motion defaults.
2. **ColorOS UXDesign / native Monet owns** palette generation.
3. **MD3E owns** semantic accent roles and selected component behavior.
4. **Vendor icons keep native geometry**; only semantic tint may change.
5. **COE hooks are component-scoped**, not package-wide.

The full per-resource TSV is intentionally generated locally by the classifier and is not committed to the public repository.
