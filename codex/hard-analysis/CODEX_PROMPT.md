# Prompt to give Codex

Work on branch `codex/coloros17-hard-analysis-20261004` of `Zhanfg/ColorOS-Monet`.

Do not implement the UI yet. Your job is to finish the four hard structural analyses described in:

- `codex/hard-analysis/TASKS.md`
- `codex/hard-analysis/STRUCTURAL_EVIDENCE.md`
- `codex/hard-analysis/SIMPLE_ANALYSIS_DONE.md`
- `codex/hard-analysis/REPORT_CONTRACT.md`

Read the existing v0.2.0 architecture documents as context, but independently verify assumptions.

Commit your reports directly to:

`codex/hard-analysis/reports/`

The repository is public. Do not commit vendor APKs, DEX blobs, decompiled proprietary source or copied artwork. Derived symbol/resource metadata is fine.

If a conclusion cannot be proven from the repository evidence, mark exactly what raw evidence is needed rather than guessing.

Priority order:
1. Settings grouped-card model.
2. UXDesign Monet/EXPRESSIVE pipeline.
3. COE migration.
4. SystemUI component map.
5. Architecture synthesis.

The most important result is an exact ColorOS 17 ownership map that lets the implementation preserve native visual behavior while adding MD3E only at verified component boundaries.
