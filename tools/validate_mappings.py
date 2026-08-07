#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from pathlib import Path

from materialize_component_specs import iter_specs

ROOT = Path(__file__).resolve().parents[1]


def validate_tsv_text(source: str, label: str) -> int:
    count = 0
    for line_no, line in enumerate(source.splitlines(), 1):
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) != 4:
            raise ValueError(f"{label}:{line_no}: expected four columns")
        if not fields[0] or not fields[1] or not fields[2]:
            raise ValueError(f"{label}:{line_no}: empty required field")
        count += 1
    return count


def validate_tsv(path: Path) -> int:
    return validate_tsv_text(path.read_text(encoding="utf-8"), str(path))


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
    component_count = 0
    component_ids: set[str] = set()
    for spec in iter_specs(ROOT / "components" / "bundles"):
        manifest = spec.get("component")
        if not isinstance(manifest, dict) or not manifest.get("id"):
            raise ValueError("component spec missing component.id")

        schema = manifest.get("schema", spec.get("format", spec.get("schema")))
        if schema not in (None, 1, "1"):
            raise ValueError(f"unsupported component schema: {schema!r}")

        component_id = str(manifest["id"])
        if component_id in component_ids:
            raise ValueError(f"duplicate component id: {component_id}")
        component_ids.add(component_id)
        component_count += 1

        files = spec.get("files")
        if not isinstance(files, dict):
            raise ValueError(f"{component_id}: missing files object")
        resources = files.get("resources.tsv")
        if not isinstance(resources, str):
            raise ValueError(f"{component_id}: missing resources.tsv")
        spec_rows += validate_tsv_text(resources, f"{component_id}/resources.tsv")

    if mapping_rows == 0 or spec_rows == 0 or component_count == 0:
        raise ValueError("empty mapping set")
    print(
        "PASS mappings: "
        f"app_rows={mapping_rows} cleanroom_rows={spec_rows} components={component_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
