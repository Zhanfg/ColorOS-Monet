#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

EXISTING = {
    "x": {
        "id": "x-monet",
        "name": "X Monet",
        "target": "com.twitter.android",
        "overlay": "coloros_monet_x",
        "category": "Applications",
    },
    "tim": {
        "id": "tim-monet",
        "name": "TIM Monet",
        "target": "com.tencent.tim",
        "overlay": "coloros_monet_tim",
        "category": "Applications",
    },
    "coolapk": {
        "id": "coolapk-monet",
        "name": "Coolapk Monet",
        "target": "com.coolapk.market",
        "overlay": "coloros_monet_coolapk",
        "category": "Applications",
    },
}

INSPIRATION = (
    "Visual hierarchy and dark-surface treatment are inspired by COUI Expressive "
    "and Material 3 Expressive community interfaces supplied by the project owner; "
    "no artwork or source code is copied."
)


def convert_mapping(root: Path, project: str, meta: dict[str, str], output: Path) -> dict:
    source = root / "components" / "app-mappings" / project
    if not source.is_dir():
        raise FileNotFoundError(source)
    out = output / meta["id"]
    out.mkdir(parents=True, exist_ok=True)
    rows: set[tuple[str, str, str, str]] = set()
    for path in sorted(source.rglob("*.tsv")):
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            fields = line.split("\t")
            if len(fields) != 4:
                raise ValueError(f"{path}:{line_no}: expected 4 columns")
            name, _role, day, night = fields
            rows.add(("color", name, day, ""))
            if night != day:
                rows.add(("color", name, night, "night"))
    lines = ["# type\tresource_name\tvalue\tconfiguration"]
    lines += ["\t".join(row) for row in sorted(rows, key=lambda r: (r[1], r[3], r[2]))]
    (out / "resources.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest = {
        "schema": 1,
        "id": meta["id"],
        "name": meta["name"],
        "version": "0.2.0",
        "target_package": meta["target"],
        "overlay_name": meta["overlay"],
        "backend": "fabricated-overlay",
        "resources": "resources.tsv",
        "min_sdk": 31,
        "description": f"APK-free semantic Monet adaptation for {meta['target']}.",
        "inspiration": INSPIRATION,
        "source_status": "clean-room-reimplemented; device-validation-required",
        "category": meta["category"],
        "default_enabled": True,
        "tags": ["apk-free", "monet", "clean-room"],
    }
    (out / "component.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    provenance = {
        "component": meta["id"],
        "target_package": meta["target"],
        "copied_application_bytecode": False,
        "copied_binary_assets": False,
        "copied_vector_path_data": False,
        "resource_rows": len(rows),
        "boundary": "Only target resource identifiers and independently reviewed semantic roles are included.",
    }
    (out / "provenance.json").write_text(
        json.dumps(provenance, indent=2) + "\n", encoding="utf-8"
    )
    (out / "unsupported.tsv").write_text(
        "type\tresource_name\tconfiguration\treason\n", encoding="utf-8"
    )
    return provenance


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, default=Path("build/component-src"))
    args = parser.parse_args()
    root = args.root.resolve()
    output = (root / args.output).resolve() if not args.output.is_absolute() else args.output
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    subprocess.run(
        [
            sys.executable,
            str(root / "tools" / "materialize_component_specs.py"),
            "--specs",
            str(root / "components" / "bundles"),
            "--output",
            str(output),
        ],
        check=True,
    )

    catalog: list[dict] = []
    for source in sorted(output.iterdir()):
        if not source.is_dir():
            continue
        provenance = source / "provenance.json"
        if provenance.exists():
            catalog.append(json.loads(provenance.read_text(encoding="utf-8")))

    for project, meta in EXISTING.items():
        catalog.append(convert_mapping(root, project, meta, output))

    (output / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"prepared {len(catalog)} component sources in {output}")
    if len(catalog) != 40:
        raise RuntimeError(f"expected 40 component sources, got {len(catalog)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
