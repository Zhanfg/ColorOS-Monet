#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def dict_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(
            (line for line in f if line.strip() and not line.lstrip().startswith("#")),
            delimiter="\t",
        ))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--homepage", type=Path, required=True)
    p.add_argument("--wrappers", type=Path, required=True)
    args = p.parse_args()

    homepage = dict_rows(args.homepage)
    wrappers = dict_rows(args.wrappers)

    wrapper_by_name: dict[str, dict[str, str]] = {}
    failures: list[str] = []

    for row in wrappers:
        name = row.get("expressive_resource", "")
        if not name:
            failures.append("wrapper row missing expressive_resource")
            continue
        if name in wrapper_by_name:
            failures.append(f"duplicate wrapper row: {name}")
        wrapper_by_name[name] = row
        if row.get("target_package") != "com.android.settings":
            failures.append(f"{name}: unexpected target_package={row.get('target_package')}")
        if row.get("evidence") != "CURRENT_TARGET_XML":
            failures.append(f"{name}: wrapper evidence is not CURRENT_TARGET_XML")
        if not row.get("wrapped_drawable"):
            failures.append(f"{name}: missing wrapped_drawable")
        if not row.get("tint_role", "").startswith("homepage_"):
            failures.append(f"{name}: unexpected tint_role={row.get('tint_role')}")

    expected = {
        row.get("preferred_candidate", "")
        for row in homepage
        if row.get("preferred_source") == "NATIVE_EXPRESSIVE"
    }
    expected.discard("")

    actual = set(wrapper_by_name)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)

    if missing:
        failures.append("homepage native Expressive candidates missing target wrapper proof: " + ", ".join(missing))
    if extra:
        failures.append("target wrapper proof rows are not in homepage native Expressive set: " + ", ".join(extra))

    if failures:
        print("Settings Expressive wrapper policy violations:")
        for failure in failures:
            print(" -", failure)
        return 1

    print(
        f"Settings Expressive wrapper policy ok: "
        f"{len(expected)} homepage wrappers proven in current target XML"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
