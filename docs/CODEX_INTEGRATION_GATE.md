# Codex integration gate

Hard structural analysis is complete. Static conclusions are integrated, but runtime/resource gates remain.

## Unfrozen for implementation

Only high-confidence decisions may now be implemented:

- removal of global/legacy hooks marked DELETE;
- exact retarget preparation marked RETARGET, with fail-closed guards;
- native-first icon/source precedence;
- diagnostic instrumentation needed to satisfy remaining evidence requests;
- packaging and policy enforcement.

## Still frozen

Do not enable or ship:

- any Settings segmented-card entry unless it appears in the exact tuple whitelist;
- any package-wide CardHook/ListHook behavior;
- automatic UXDesign/theme-style mutation;
- SystemUI QS/media/notification/volume/clock visual hooks without the listed runtime/XML gate;
- any NEEDS_EVIDENCE COE hook.

## Evidence source

Frozen reports:

- `codex/hard-analysis/reports/00_ARCHITECTURE_SYNTHESIS.md`
- `01_UXDESIGN_MONET_PIPELINE.md`
- `02_SETTINGS_GROUPED_CARD_MODEL.md`
- `03_SYSTEMUI_COMPONENT_MAP.md`
- `04_COE_293_ANDROID17_MIGRATION.md`

The reports are static evidence. Runtime uncertainty is not permission to guess.
