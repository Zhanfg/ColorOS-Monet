# Post-Codex integration plan

Tracking issue: #16

Hard analysis completed at:
`21c0f02ec27774f0865db9d7eb12601f79aaa79b`

Current implementation branch:
`coloros17-md3e-v0.2.0`

## Completed

- [x] Five hard-analysis reports landed and were copied into the implementation branch.
- [x] Native Settings grouped-card ownership established.
- [x] UXDesign/SystemUI Monet ownership separated.
- [x] COE hook keep/retarget/replace/delete matrix established.
- [x] SystemUI QS/notification/media/volume/clock owners separated.
- [x] Package-wide CardHook/ListHook rejected.
- [x] Global MonetColorSpec2025 replacement rejected.
- [x] Automatic ColorOS theme-style mutation removed from shipping path.
- [x] Generic vendor artwork path retired.
- [x] Official Material Symbols upstream pinned.
- [x] Native ColorOS/AOSP Expressive assets take precedence over Material Symbols.
- [x] CI architecture-policy lints added.
- [x] Semantic MD3E layer defaults off until runtime consumer validation.

## Current implementation order

1. Evidence closure
   - collect exact runtime provenance with `ColorOS17_MD3E_RuntimeEvidence_v1.sh`;
   - obtain only the narrow XML/framework/helper evidence requested by Codex.

2. Settings
   - segmented whitelist remains empty;
   - add a component only after exact Activity/Fragment/adapter/key/view/layout proof.

3. UXDesign / Monet
   - consume the currently active native palette;
   - no boot-time style forcing;
   - native user theme changes always win.

4. COE
   - source-level migration only;
   - DELETE actions first, then RETARGET/REPLACE with fail-closed guards;
   - temporary binary no-op patcher remains under `experiments/` only.

5. SystemUI
   - QS, notification, media, volume and clock remain independent contracts;
   - preserve native blur, state machines, geometry and motion.

6. One-reboot validation
   - only after component gates above are satisfied;
   - build one candidate, reboot once, collect post-boot evidence and visual regression.

## Release gate

No alpha is promoted merely because CI is green. A candidate must also have:

- no global COUI radius/divider/card override;
- no package-wide CardHook/ListHook;
- no parallel Monet generator;
- no unconditional theme-style mutation;
- no generic replacement artwork;
- exact component whitelist entries for every non-native hook;
- light/dark/current-wallpaper regression coverage.
