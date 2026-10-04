#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

FAMILIES = (
    "materialsymbolsrounded",
    "materialsymbolsoutlined",
    "materialsymbolssharp",
)

def variants(directory: Path) -> list[str]:
    return sorted(p.name for p in directory.glob("*.xml") if p.is_file())

def main() -> int:
    p = argparse.ArgumentParser(
        description="Index a local checkout of google/material-design-icons for ColorOS mapping."
    )
    p.add_argument("--upstream", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()

    root = args.upstream / "symbols" / "android"
    if not root.is_dir():
        raise SystemExit(f"missing Material Symbols Android tree: {root}")

    rows = []
    for symbol_dir in sorted(x for x in root.iterdir() if x.is_dir()):
        symbol = symbol_dir.name
        for family in FAMILIES:
            d = symbol_dir / family
            if not d.is_dir():
                continue
            files = variants(d)
            if not files:
                continue

            base20 = f"{symbol}_20px.xml"
            base24 = f"{symbol}_24px.xml"
            base40 = f"{symbol}_40px.xml"
            base48 = f"{symbol}_48px.xml"
            fill24 = f"{symbol}_fill1_24px.xml"

            rows.append({
                "symbol": symbol,
                "family": family,
                "has_20": "1" if base20 in files else "0",
                "has_24": "1" if base24 in files else "0",
                "has_40": "1" if base40 in files else "0",
                "has_48": "1" if base48 in files else "0",
                "has_fill1_24": "1" if fill24 in files else "0",
                "variant_count": str(len(files)),
                "variants": ";".join(files),
            })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "symbol", "family", "has_20", "has_24", "has_40", "has_48",
        "has_fill1_24", "variant_count", "variants",
    ]
    with args.output.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
        w.writeheader()
        w.writerows(rows)

    symbols = len({r["symbol"] for r in rows})
    print(f"indexed {symbols} symbols / {len(rows)} family rows")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
