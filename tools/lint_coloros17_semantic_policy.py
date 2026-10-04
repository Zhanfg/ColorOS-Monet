#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "compat/coloros17/md3e_semantic_accent.tsv"

ALLOWED_NAMES = {
    "coui_color_additional_blue",
    "coui_color_blue",
    "coui_color_primary_blue",
    "coui_color_primary_on_popup_blue",
    "coui_color_primary_text_blue",
    "colorPrimary",
}
LIGHT = "@android:color/system_primary_light"
DARK = "@android:color/system_primary_dark"
DENY = re.compile(
    r"(background|surface|card|divider|separator|outline|pressed|press|ripple|"
    r"disabled|selected|neutral|scrim|shadow|corner|radius|round|blur|elevation)",
    re.I,
)

def main() -> int:
    rows = []
    with TABLE.open(encoding="utf-8", newline="") as f:
        for raw in f:
            if not raw.strip() or raw.lstrip().startswith("#"):
                continue
            row = next(csv.reader([raw], delimiter="\t"))
            if len(row) != 5:
                raise SystemExit(f"invalid column count: {raw.rstrip()}")
            rows.append(row)

    seen = set()
    errors = []
    for key, target, name, light, dark in rows:
        ident = (target, name)
        if ident in seen:
            errors.append(f"duplicate {target}:{name}")
        seen.add(ident)

        if name not in ALLOWED_NAMES:
            errors.append(f"resource outside semantic allowlist: {target}:{name}")
        if DENY.search(name):
            errors.append(f"forbidden structural/state token: {target}:{name}")
        if light != LIGHT or dark != DARK:
            errors.append(
                f"unexpected palette mapping {target}:{name}: {light} / {dark}"
            )
        if not key or not target:
            errors.append(f"empty key/target: {raw!r}")

    if not rows:
        errors.append("semantic table is empty")

    if errors:
        print("semantic policy violations:")
        for err in errors:
            print(" -", err)
        return 1

    packages = len({target for _, target, _, _, _ in rows})
    print(f"semantic policy ok: {len(rows)} resources across {packages} packages")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
