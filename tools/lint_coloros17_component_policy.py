#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WHITELIST = ROOT / "compat/coloros17/settings_segmented_whitelist.tsv"
COE = ROOT / "compat/coloros17/coe_hook_policy.tsv"

FORBIDDEN_KEEP = {
    "CardHook",
    "ListHook",
    "MonetColorSpec2025Hook",
    "ClassicQsHook",
    "QsHighlightCornerHook",
    "QsHighlightCornerHookOld",
    "QsThreeStageCornerHook",
    "StockVolumeDialogHook",
    "ScrimHook",
    "ScrimAltHook",
    "PixelLockscreenClockHook",
    "GestureHook",
    "OverscrollHook",
    "ToolbarHook",
    "CouiToolbarHookFade",
    "ToolbarHookScale",
    "PopupHook",
    "SettingsThemeUtilsHook",
    "IconMaskOverlayHook",
    "DockHook",
    "DockHookExp",
    "MaterialHook",
    "RecentsStyleHook",
}

def rows(path: Path):
    with path.open(encoding="utf-8", newline="") as f:
        return [
            r for r in csv.reader(
                (line for line in f if line.strip() and not line.lstrip().startswith("#")),
                delimiter="\t",
            )
        ]

def main() -> int:
    failures = []

    wl = rows(WHITELIST)
    # Header-only is expected until runtime/XML evidence exists.
    for row in wl[1:]:
        if len(row) != 8:
            failures.append(f"invalid Settings whitelist row: {row}")
            continue
        activity, fragment, adapter, key, view, layout, feature, evidence = row
        joined = "\t".join(row)
        if "*" in joined or not all((activity, fragment, adapter, key, view, layout, feature, evidence)):
            failures.append(f"non-exact Settings whitelist row: {row}")

    policy = rows(COE)
    for row in policy[1:]:
        if len(row) != 4:
            failures.append(f"invalid COE policy row: {row}")
            continue
        hook, action, confidence, _ = row
        if action not in {"KEEP","DELETE","REPLACE","RETARGET","NEEDS_EVIDENCE"}:
            failures.append(f"invalid COE action: {hook}={action}")
        if confidence not in {"HIGH","MEDIUM","LOW"}:
            failures.append(f"invalid COE confidence: {hook}={confidence}")
        if hook in FORBIDDEN_KEEP and action == "KEEP":
            failures.append(f"forbidden legacy/global hook marked KEEP: {hook}")

    if failures:
        print("component policy violations:")
        for failure in failures:
            print(" -", failure)
        return 1

    print(f"component policy ok: settings_whitelist_rows={max(0,len(wl)-1)} coe_hooks={max(0,len(policy)-1)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
