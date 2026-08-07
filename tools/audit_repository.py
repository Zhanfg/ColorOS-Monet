#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import gzip
import json
import lzma
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_SUFFIXES = {".apk", ".xapk", ".apks", ".jks", ".keystore", ".p12", ".pfx"}
SENSITIVE = re.compile(
    r"(?i)(?:sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)"
)


def main() -> int:
    failures: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts or "build" in path.parts or "target" in path.parts:
            continue
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            failures.append(f"forbidden file: {path.relative_to(ROOT)}")
        if path.stat().st_size <= 2_000_000:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if SENSITIVE.search(text):
                failures.append(f"possible secret: {path.relative_to(ROOT)}")

    bundle_dir = ROOT / "components" / "bundles"
    bundle_paths = sorted(bundle_dir.glob("cleanroom-*.jsonl")) + sorted(bundle_dir.glob("cleanroom-*.jsonl.gz")) + sorted(bundle_dir.glob("cleanroom-*.jsonl.xz"))
    specs: list[tuple[str, dict[str, object]]] = []
    for bundle_path in bundle_paths:
        try:
            if bundle_path.suffix == ".gz":
                text = gzip.decompress(bundle_path.read_bytes()).decode("utf-8")
            elif bundle_path.suffix == ".xz":
                text = lzma.decompress(bundle_path.read_bytes()).decode("utf-8")
            else:
                text = bundle_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            failures.append(f"invalid component bundle {bundle_path.name}: {exc}")
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                spec = json.loads(line)
            except json.JSONDecodeError as exc:
                failures.append(f"invalid JSONL {bundle_path.name}:{line_number}: {exc}")
                continue
            specs.append((f"{bundle_path.name}:{line_number}", spec))

    if len(specs) != 37:
        failures.append(f"expected 37 clean-room component specs, found {len(specs)}")
    ids = set()
    for location, spec in specs:
        manifest = spec.get("component", {})
        if not isinstance(manifest, dict):
            failures.append(f"invalid component manifest: {location}")
            continue
        component_id = manifest.get("id")
        if not isinstance(component_id, str) or not component_id:
            failures.append(f"missing component id: {location}")
            continue
        if component_id in ids:
            failures.append(f"duplicate component id: {component_id}")
        ids.add(component_id)
        if manifest.get("backend") != "fabricated-overlay":
            failures.append(f"unexpected backend: {location}")
        files = spec.get("files", {})
        if not isinstance(files, dict):
            failures.append(f"invalid files table: {location}")
            continue
        provenance = files.get("provenance.json", "{}")
        if not isinstance(provenance, str):
            failures.append(f"invalid provenance payload type: {location}")
            continue
        try:
            provenance_data = json.loads(provenance)
        except json.JSONDecodeError:
            failures.append(f"invalid provenance: {location}")
            continue
        for field in ("copied_application_bytecode", "copied_binary_assets", "copied_vector_path_data"):
            if provenance_data.get(field) is True:
                failures.append(f"clean-room violation {field}: {location}")

    required = [
        "runtime/Cargo.toml", "runtime/src/main.rs", "module/customize.sh",
        "module/post-fs-data.sh", "module/service.sh", "module/action.sh",
        "module/uninstall.sh", "docs/COMPONENT_FORMAT.md",
    ]
    for name in required:
        if not (ROOT / name).is_file():
            failures.append(f"missing required file: {name}")

    if failures:
        raise SystemExit("\n".join(failures))
    print(f"PASS repository audit: bundled_specs={len(specs)} forbidden_payloads=0 secrets=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
