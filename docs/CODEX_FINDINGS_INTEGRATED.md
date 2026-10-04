# Codex hard-analysis integration status

Hard-analysis branch completed at:

`21c0f02ec27774f0865db9d7eb12601f79aaa79b`

The five reports are now copied into the v0.2.0 branch as frozen evidence.

## High-confidence decisions accepted

- Keep ColorOS/COUI continuous grouped-list geometry, smooth paths, divider state and row interaction.
- Settings segmented-card whitelist starts empty.
- Delete the idea that `mCardBackgroundColor` was globally removed; the analyzed Settings DEX still declares it on the superclass.
- Delete global `MonetColorSpec2025Hook`; native SystemUI uses SPEC_2026 and owns fabricated-overlay generation.
- Do not suppress native QS Lottie globally; `QSIconViewProxy` still exists.
- Replace old media-card reconstruction with a future exact plugin component contract.
- Treat `OplusVolumeDialogImpl` as the OPlus volume implementation family; do not target AOSP VolumeDialogImpl as the primary migration owner.
- Treat UXDesign EXPRESSIVE palette selection and Settings Expressive UI gating as different states.
- Never rewrite ColorOS theme style at boot.
- Prefer current native Expressive resources before AOSP/Material Symbols fallback.

## Blockers that remain real

Static analysis did not authorize a shipping segmented-card hook, SystemUI visual hook, or automatic theme-style mutation.

Remaining release gates:

- exact Settings resource XML + runtime tuple for any segmented component;
- actual runtime classloader/provenance for the historical NoSuchFieldError;
- SystemUI active-instance traces for QS/notification/media/volume/clock;
- limited framework/volume helper bytecode requested by the reports;
- runtime verification that user theme changes remain authoritative.

## Current shipping behavior

Until those gates are satisfied:

- `md3e_semantic` defaults **off**;
- the semantic RRO set remains buildable and manually opt-in for controlled testing;
- no CardHook/ListHook is shipped by this repository;
- no automatic EXPRESSIVE theme-style helper is shipped;
- no generic replacement artwork is shipped.

## Policy files

- `compat/coloros17/settings_segmented_whitelist.tsv`
- `compat/coloros17/coe_hook_policy.tsv`
- `compat/coloros17/systemui_component_policy.tsv`

CI treats these files as architecture contracts, not informal notes.
