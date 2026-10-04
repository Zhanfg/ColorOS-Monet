#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import difflib
import re
from pathlib import Path

PREFIXES = ("ic_", "icon_", "menu_ic_", "affordance_")
SUFFIX_RE = re.compile(
    r"(_icon|_ic|_(16|18|20|22|24|32|36|40|48)(dp|px)?|_black|_white|"
    r"_dark|_light|_normal|_pressed|_disabled|_filled|_themed)$"
)

def normalize(name: str) -> str:
    value = name.lower()
    changed = True
    while changed:
        changed = False
        for prefix in PREFIXES:
            if value.startswith(prefix):
                value = value[len(prefix):]
                changed = True
        new = SUFFIX_RE.sub("", value)
        if new != value:
            value = new
            changed = True
    return value.strip("_")

def read_aliases(path: Path) -> dict[str, tuple[str, str]]:
    aliases = {}
    with path.open(encoding="utf-8", newline="") as f:
        for raw in f:
            if not raw.strip() or raw.lstrip().startswith("#"):
                continue
            name, symbol, confidence, *_ = next(csv.reader([raw], delimiter="\t"))
            aliases[name] = (symbol, confidence)
    return aliases

def upstream_symbols(root: Path) -> set[str]:
    android = root / "symbols" / "android"
    if not android.is_dir():
        raise RuntimeError(f"missing upstream symbols tree: {android}")
    return {p.name for p in android.iterdir() if p.is_dir()}

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--inventory", type=Path, required=True)
    p.add_argument("--upstream", type=Path, required=True)
    p.add_argument("--aliases", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()

    symbols = upstream_symbols(args.upstream)
    aliases = read_aliases(args.aliases)
    rows = []

    with args.inventory.open(encoding="utf-8", newline="") as f:
        for item in csv.DictReader(f, delimiter="\t"):
            if item["classification"] != "GENERIC_CANDIDATE":
                continue
            normalized = normalize(item["resource_name"])

            candidates: list[tuple[str, float, str]] = []
            if normalized in symbols:
                candidates.append((normalized, 1.0, "exact_normalized"))
            if normalized in aliases and aliases[normalized][0] in symbols:
                candidates.append((aliases[normalized][0], 0.98, "curated_alias"))

            close = difflib.get_close_matches(normalized, sorted(symbols), n=5, cutoff=0.72)
            for symbol in close:
                score = difflib.SequenceMatcher(None, normalized, symbol).ratio()
                candidates.append((symbol, score, "fuzzy_name"))

            best = {}
            for symbol, score, reason in candidates:
                if symbol not in best or score > best[symbol][0]:
                    best[symbol] = (score, reason)

            ranked = sorted(
                ((symbol, score, reason) for symbol, (score, reason) in best.items()),
                key=lambda x: (-x[1], x[0]),
            )[:3]

            out = dict(item)
            out["normalized_name"] = normalized
            for i in range(3):
                if i < len(ranked):
                    symbol, score, reason = ranked[i]
                    out[f"candidate_{i+1}"] = symbol
                    out[f"score_{i+1}"] = f"{score:.3f}"
                    out[f"reason_{i+1}"] = reason
                else:
                    out[f"candidate_{i+1}"] = ""
                    out[f"score_{i+1}"] = ""
                    out[f"reason_{i+1}"] = ""
            rows.append(out)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else [
        "target_package","resource_type","resource_name","classification",
        "source_target","normalized_name","candidate_1","score_1","reason_1",
        "candidate_2","score_2","reason_2","candidate_3","score_3","reason_3",
    ]
    with args.output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    exact = sum(1 for r in rows if r.get("reason_1") in {"exact_normalized", "curated_alias"})
    print(f"candidate_rows={len(rows)}")
    print(f"exact_or_alias_top1={exact}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
