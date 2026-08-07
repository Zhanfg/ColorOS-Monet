#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import argparse
import gzip
import json
import lzma
import shutil
from pathlib import Path, PurePosixPath


def safe_relative(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"unsafe component path: {name}")
    return path


def iter_specs(source: Path):
    bundles = sorted(source.glob("*.jsonl")) + sorted(source.glob("*.jsonl.gz")) + sorted(source.glob("*.jsonl.xz"))
    if bundles:
        for bundle in bundles:
            if bundle.suffix == ".gz":
                text = gzip.decompress(bundle.read_bytes()).decode("utf-8")
            elif bundle.suffix == ".xz":
                text = lzma.decompress(bundle.read_bytes()).decode("utf-8")
            else:
                text = bundle.read_text(encoding="utf-8")
            for line_no, line in enumerate(text.splitlines(), 1):
                if not line.strip():
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(f"{bundle}:{line_no}: {error}") from error
        return
    for spec_path in sorted(source.glob("*.json")):
        if spec_path.name != "catalog.json":
            yield json.loads(spec_path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--specs", type=Path, default=Path("components/bundles"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    specs = args.specs.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    count = 0
    seen: set[str] = set()
    for spec in iter_specs(specs):
        if spec.get("format") != 1:
            raise ValueError("unsupported component spec format")
        manifest = spec["component"]
        component_id = manifest["id"]
        if component_id in seen:
            raise ValueError(f"duplicate component id: {component_id}")
        seen.add(component_id)
        destination = output / component_id
        if destination.exists():
            shutil.rmtree(destination)
        destination.mkdir(parents=True)
        (destination / "component.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        for name, content in spec["files"].items():
            relative = safe_relative(name)
            path = destination.joinpath(*relative.parts)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        count += 1
    print(f"materialized {count} component specs into {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
