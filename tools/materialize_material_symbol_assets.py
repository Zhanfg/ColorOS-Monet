#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
from pathlib import Path

APPROVED = {"MATERIAL_SYMBOL", "STATEFUL_SYMBOL"}

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def asset_name(symbol: str, size: str, variant: str) -> str:
    suffix = "" if variant in {"", "base"} else f"_{variant}"
    return f"{symbol}{suffix}_{size}px.xml"

def safe_package(package: str) -> str:
    return package.replace(".", "_").replace("/", "_")

def main() -> int:
    p = argparse.ArgumentParser(
        description="Materialize only reviewed Material Symbols from the pinned upstream checkout."
    )
    p.add_argument("--upstream", type=Path, required=True)
    p.add_argument("--mapping", type=Path, required=True)
    p.add_argument("--upstream-ref", required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()

    android = args.upstream / "symbols" / "android"
    if not android.is_dir():
        raise RuntimeError(f"missing Material Symbols Android tree: {android}")

    shutil.rmtree(args.output, ignore_errors=True)
    args.output.mkdir(parents=True, exist_ok=True)

    manifest = []
    with args.mapping.open(encoding="utf-8", newline="") as f:
        for raw in f:
            if not raw.strip() or raw.lstrip().startswith("#"):
                continue
            row = next(csv.reader([raw], delimiter="\t"))
            if len(row) != 11:
                raise RuntimeError(f"invalid mapping row: {raw.rstrip()}")

            (
                target_package,
                target_resource,
                semantic_role,
                symbol,
                family,
                size,
                unselected_variant,
                selected_variant,
                action,
                confidence,
                notes,
            ) = row

            if action not in APPROVED:
                continue

            package_dir = args.output / safe_package(target_package) / "res" / "drawable"
            package_dir.mkdir(parents=True, exist_ok=True)

            variants = [("base", unselected_variant, target_resource)]
            if action == "STATEFUL_SYMBOL":
                variants.append(
                    ("selected", selected_variant, f"{target_resource}__selected")
                )

            for state, variant, output_name in variants:
                upstream_name = asset_name(symbol, size, variant)
                src = android / symbol / family / upstream_name
                if not src.is_file():
                    raise RuntimeError(
                        f"approved mapping missing upstream asset: "
                        f"{symbol}/{family}/{upstream_name}"
                    )

                dst = package_dir / f"{output_name}.xml"
                shutil.copy2(src, dst)
                manifest.append(
                    [
                        target_package,
                        target_resource,
                        semantic_role,
                        action,
                        state,
                        symbol,
                        family,
                        size,
                        variant,
                        str(src.relative_to(args.upstream)),
                        str(dst.relative_to(args.output)),
                        args.upstream_ref,
                        sha256(src),
                    ]
                )

    manifest_path = args.output / "MATERIAL_SYMBOLS_MANIFEST.tsv"
    with manifest_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(
            [
                "target_package",
                "target_resource",
                "semantic_role",
                "action",
                "state",
                "symbol",
                "family",
                "size",
                "variant",
                "upstream_path",
                "output_path",
                "upstream_ref",
                "sha256",
            ]
        )
        w.writerows(manifest)

    print(f"approved_assets={len(manifest)}")
    print(f"manifest={manifest_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
