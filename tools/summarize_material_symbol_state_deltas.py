#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--review-root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()

    rows = list(csv.DictReader(args.manifest.open(encoding="utf-8", newline=""), delimiter="\t"))
    by_key: dict[str, dict[str, dict[str, str]]] = {}
    for row in rows:
        by_key.setdefault(row["key"], {})[row["state"]] = row

    out = []
    failures = []
    for key, states in sorted(by_key.items()):
        base = states.get("base")
        selected = states.get("selected")
        if not base or not selected:
            failures.append(f"{key}: missing base/selected pair")
            continue

        base_file = args.review_root / "candidates" / key / "base.xml"
        selected_file = args.review_root / "candidates" / key / "selected.xml"
        if not base_file.is_file() or not selected_file.is_file():
            failures.append(f"{key}: materialized XML pair missing")
            continue

        bsha = sha256(base_file)
        ssha = sha256(selected_file)
        changed = bsha != ssha
        out.append({
            "key": key,
            "symbol": base["symbol"],
            "family": base["family"],
            "size": base["size"],
            "base_sha256": bsha,
            "selected_sha256": ssha,
            "fill1_changes_xml": "1" if changed else "0",
            "state_policy": "STATEFUL_CANDIDATE" if changed else "STATIC_GLYPH_ONLY",
        })

    if failures:
        for failure in failures:
            print("FAIL", failure)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "key", "symbol", "family", "size",
        "base_sha256", "selected_sha256",
        "fill1_changes_xml", "state_policy",
    ]
    with args.output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(out)

    stateful = sum(r["fill1_changes_xml"] == "1" for r in out)
    print(f"rows={len(out)} stateful={stateful} static={len(out)-stateful}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
