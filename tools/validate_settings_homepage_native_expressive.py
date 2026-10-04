#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_MAP = ROOT / "compat/material-symbols/settings_homepage_full_source_map.tsv"
WRAPPERS = ROOT / "compat/material-symbols/coloros17_settings_expressive_wrappers.tsv"

def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))

def main() -> int:
    wrapper_rows = read_tsv(WRAPPERS)
    wrappers = {r["expressive_resource"]: r for r in wrapper_rows}
    failures = []
    native_rows = 0

    for row in read_tsv(SOURCE_MAP):
        if row["preferred_source"] != "NATIVE_EXPRESSIVE":
            continue
        native_rows += 1
        candidate = row["preferred_candidate"].removeprefix("drawable/").removeprefix("@drawable/")
        wrapper = wrappers.get(candidate)
        if not wrapper:
            failures.append(f"{row['key']}: no verified TintDrawable wrapper for {candidate}")
            continue
        if wrapper["target_package"] != "com.android.settings":
            failures.append(f"{row['key']}: unexpected target package for {candidate}")
        if wrapper["evidence"] != "CURRENT_TARGET_BINARY_XML":
            failures.append(f"{row['key']}: weak wrapper evidence for {candidate}")
        if not wrapper["wrapped_drawable"]:
            failures.append(f"{row['key']}: empty wrapped glyph for {candidate}")

    if failures:
        print("native Expressive homepage policy failed:")
        for failure in failures:
            print(" -", failure)
        return 1

    print(
        f"native Expressive homepage policy ok: "
        f"{native_rows} mapped rows / {len(wrapper_rows)} verified wrappers"
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
