#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate_tsv(path: Path) -> int:
    count = 0
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) != 4:
            raise ValueError(f"{path}:{line_no}: expected four columns")
        if not fields[0] or not fields[1] or not fields[2]:
            raise ValueError(f"{path}:{line_no}: empty required field")
        count += 1
    return count


def main() -> int:
    mapping_rows = 0
    for project in ("x", "tim", "coolapk"):
        folder = ROOT / "components" / "app-mappings" / project
        files = sorted(folder.glob("*.tsv"))
        if not files:
            raise FileNotFoundError(folder)
        for path in files:
            mapping_rows += validate_tsv(path)

    spec_rows = 0
    for path in sorted((ROOT / "components" / "specs").glob("*.json")):
        if path.name == "catalog.json":
            continue
        spec = json.loads(path.read_text(encoding="utf-8"))
        resources = spec["files"].get("resources.tsv")
        if resources is None:
            raise ValueError(f"{path}: missing resources.tsv")
        for line in resources.splitlines():
            if line and not line.startswith("#"):
                fields = line.split("\t")
                if len(fields) != 4:
                    raise ValueError(f"{path}: malformed embedded resource row")
                spec_rows += 1
    if mapping_rows == 0 or spec_rows == 0:
        raise ValueError("empty mapping set")
    print(f"PASS mappings: app_rows={mapping_rows} cleanroom_rows={spec_rows}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
