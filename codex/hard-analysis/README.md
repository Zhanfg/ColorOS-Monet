# Codex handoff: ColorOS 17 × MD3E hard analysis

This branch is an analysis handoff, not a shipping branch.

Frozen implementation base: `coloros17-md3e-v0.2.0` at `d6206a7885608cc6618f4dc4627c62587f19bd1c`.

## Goal

Establish the real ColorOS 17 design/runtime structure before changing the v0.2.0 implementation again.

The target design is **ColorOS 17 native-first + Material 3 Expressive augmentation**:

- preserve native ColorOS geometry, blur, translucency, icon artwork, grouping and useful motion;
- use the ROM's real dynamic-color pipeline instead of inventing a parallel Monet engine;
- add MD3E only at semantic/component boundaries that are actually verified;
- eliminate package-wide card/list hacks.

## Scope delegated to Codex

Only the hard/ambiguous parts are delegated:

1. UXDesign / Monet / EXPRESSIVE pipeline.
2. Settings grouped-card/list implementation and ColorOS 17 COUI changes.
3. SystemUI + SystemUIPlugin component boundaries (QS/media/notification/volume/blur/motion).
4. COE 2.9.3 hook migration and Android 17 compatibility.

Simple RRO/resource-table work has already been analyzed; see `SIMPLE_ANALYSIS_DONE.md`.

## Important constraints

- Do **not** redesign the project while investigating.
- Do **not** assume a class/field exists because it existed on ColorOS 16.
- Separate observed fact from inference.
- Every conclusion about a runtime hook must name the exact class/method/field or resource involved.
- Prefer a minimal compatibility layer over broad package-wide hooks.
- Do not commit proprietary APK/DEX/drawable payloads to this public repository.
- If bytecode evidence is unavailable, mark the point as `NEEDS_RAW_BYTECODE` instead of guessing.

## Output

Commit analysis only under:

`codex/hard-analysis/reports/`

Use the report contract in `REPORT_CONTRACT.md`.
