# Post-Codex integration plan

Tracking issue: #16

Current clean baseline:
- branch: `coloros17-md3e-v0.2.0`
- semantic layer: 106 locally proven accent resources across 14 system packages
- no generic vendor artwork
- no legacy third-party overlays in the shipping module
- no automatic ColorOS theme-style mutation

## Freeze boundary while hard analysis runs

Do not modify:

- Settings grouped/segmented card hooks;
- UXDesign palette/style ownership;
- SystemUI QS/media/notification/volume/clock hooks;
- COE Android 17 retargeting.

Allowed parallel work:

- semantic provenance;
- CI/policy gates;
- packaging/update safety;
- read-only diagnostics;
- ROM-update compatibility checks;
- visual-regression capture tooling.

## Integration order

1. **Settings grouped-card report**
   - establish native first/middle/last/single ownership;
   - implement only an explicit segmented-card whitelist.

2. **UXDesign Monet report**
   - settle whether v0.2.0 consumes active colors only or may request a native variant;
   - user theme changes must always win over module defaults.

3. **COE migration report**
   - replace binary P0 no-op with source-level keep/retarget/replace/delete decisions;
   - all hooks fail closed.

4. **SystemUI component map**
   - implement QS, notification, media, volume and clock separately;
   - preserve native blur/translucency and plugin ownership.

5. **Architecture synthesis**
   - resolve contradictions across all four reports before implementation merge.

## Validation gate

A flashable alpha is not produced merely because each component compiles.

Before the next on-device reboot candidate:

- all hard-analysis reports are present;
- architecture contradictions are resolved;
- CI semantic-policy checks pass;
- no global COUI radius/divider/card override is present;
- no package-wide CardHook/ListHook is present;
- no generic replacement artwork is present;
- no unconditional theme-style mutation is present;
- light/dark + current-wallpaper visual regression plan is generated.

Only then build a single one-reboot validation candidate.
