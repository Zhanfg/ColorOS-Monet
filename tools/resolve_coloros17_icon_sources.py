#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

def read_tsv(path: Path) -> list[list[str]]:
    rows = []
    with path.open(encoding="utf-8", newline="") as f:
        for raw in f:
            if not raw.strip() or raw.lstrip().startswith("#"):
                continue
            rows.append(next(csv.reader([raw], delimiter="\t")))
    return rows

def main() -> int:
    p = argparse.ArgumentParser(
        description="Resolve ColorOS icon source precedence without emitting any artwork."
    )
    p.add_argument("--native-pairs", type=Path, required=True)
    p.add_argument("--native-map", type=Path, required=True)
    p.add_argument("--material-map", type=Path, required=True)
    p.add_argument("--oplus-homepage", type=Path)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()

    exact_pairs = {}
    for row in read_tsv(args.native_pairs):
        if len(row) < 6 or row[0] == "target_package":
            continue
        package, typ, base, expressive, evidence, source = row[:6]
        exact_pairs[(package, base)] = (expressive, evidence)

    curated_native = {}
    for row in read_tsv(args.native_map):
        if len(row) < 7:
            continue
        package, semantic, base, expressive, upstream, decision, verification = row[:7]
        curated_native[(package, base)] = {
            "semantic": semantic,
            "expressive": expressive,
            "verification": verification,
        }

    material = {}
    for row in read_tsv(args.material_map):
        if len(row) < 11:
            continue
        package, base, semantic, symbol, family, size, off, on, action, confidence, notes = row[:11]
        material[(package, base)] = {
            "semantic": semantic,
            "symbol": symbol,
            "family": family,
            "size": size,
            "action": action,
            "confidence": confidence,
            "notes": notes,
        }

    oplus_homepage = set()
    if args.oplus_homepage:
        for row in read_tsv(args.oplus_homepage):
            if len(row) < 3 or row[0] == "preference_key":
                continue
            oplus_homepage.add(("com.android.settings", row[2]))

    keys = sorted(set(exact_pairs) | set(curated_native) | set(material) | oplus_homepage)
    out = []
    for package, base in keys:
        exact = exact_pairs.get((package, base))
        native = curated_native.get((package, base))
        mat = material.get((package, base))

        if (package, base) in oplus_homepage:
            source = "KEEP_NATIVE_OPLUS_HOMEPAGE"
            selected = base
            confidence = "HIGH"
            gate = "VERIFIED_OPLUS_XML_AND_DEX_OWNER"
        elif exact:
            source = "COLOROS_NATIVE_EXPRESSIVE"
            selected = exact[0]
            confidence = "HIGH"
            gate = "PENDING_CONSUMER_TRACE"
        elif native:
            source = "COLOROS_NATIVE_EXPRESSIVE_CANDIDATE"
            selected = native["expressive"]
            confidence = "MEDIUM"
            gate = native["verification"]
        elif mat and mat["action"] != "KEEP_NATIVE":
            source = "GOOGLE_MATERIAL_SYMBOL_CANDIDATE"
            selected = mat["symbol"]
            confidence = mat["confidence"]
            gate = "PENDING_CONSUMER_TRACE"
        else:
            source = "KEEP_NATIVE"
            selected = ""
            confidence = mat["confidence"] if mat else "HIGH"
            gate = "NO_AUTOMATIC_REPLACEMENT"

        out.append([
            package,
            base,
            native["semantic"] if native else (mat["semantic"] if mat else ""),
            source,
            selected,
            confidence,
            gate,
            mat["symbol"] if mat else "",
        ])

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow([
            "target_package","base_resource","semantic_role","preferred_source",
            "selected_asset_or_symbol","confidence","gate","material_fallback",
        ])
        w.writerows(out)

    counts = {}
    for row in out:
        counts[row[3]] = counts.get(row[3], 0) + 1
    print(f"resolved_rows={len(out)}")
    for key in sorted(counts):
        print(f"{key}={counts[key]}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
