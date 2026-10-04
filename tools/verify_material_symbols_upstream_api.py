#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import urllib.request
from pathlib import Path

API = "https://api.github.com"

def read_lock(path: Path) -> dict[str, str]:
    out = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        out[key.strip()] = value.strip()
    return out

def api_get(path: str, token: str) -> dict:
    req = urllib.request.Request(
        API + path,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "ColorOS-Monet-MaterialSymbolsVerifier",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))

def asset_name(symbol: str, size: str, variant: str) -> str:
    suffix = "" if variant in {"", "base"} else f"_{variant}"
    return f"{symbol}{suffix}_{size}px.xml"

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--lock", type=Path, required=True)
    p.add_argument("--mapping", type=Path, required=True)
    p.add_argument("--catalog-output", type=Path, required=True)
    p.add_argument("--capabilities-output", type=Path, required=True)
    args = p.parse_args()

    lock = read_lock(args.lock)
    repo = lock["repository"].removesuffix(".git").split("github.com/", 1)[1]
    ref = lock["ref"]
    android_tree_sha = lock["android_tree_sha"]
    token = os.environ.get("GITHUB_TOKEN", "")

    # Verify the pinned commit exists and matches exactly.
    commit = api_get(f"/repos/{repo}/commits/{ref}", token)
    actual = commit["sha"]
    if actual != ref:
        raise SystemExit(f"pinned ref mismatch: expected {ref}, got {actual}")

    android_tree = api_get(f"/repos/{repo}/git/trees/{android_tree_sha}", token)
    if android_tree.get("truncated"):
        raise SystemExit("android symbol root tree unexpectedly truncated")

    symbols = {
        item["path"]: item["sha"]
        for item in android_tree.get("tree", [])
        if item.get("type") == "tree"
    }

    expected_count = int(lock.get("symbol_directory_count", "0") or 0)
    if expected_count and len(symbols) != expected_count:
        raise SystemExit(
            f"symbol directory count changed: expected {expected_count}, got {len(symbols)}"
        )

    args.catalog_output.parent.mkdir(parents=True, exist_ok=True)
    args.catalog_output.write_text(
        "symbol\n" + "\n".join(sorted(symbols)) + "\n",
        encoding="utf-8",
    )

    rows = []
    with args.mapping.open(encoding="utf-8", newline="") as f:
        for raw in f:
            if not raw.strip() or raw.lstrip().startswith("#"):
                continue
            cols = next(csv.reader([raw], delimiter="\t"))
            if len(cols) != 11:
                raise SystemExit(f"invalid mapping row: {raw.rstrip()}")
            rows.append(cols)

    by_symbol: dict[str, set[str]] = {}
    for row in rows:
        symbol, family, size, off, on, action = row[3], row[4], row[5], row[6], row[7], row[8]
        if symbol not in symbols:
            raise SystemExit(f"mapped symbol missing from upstream: {symbol}")
        wanted = {
            f"{family}/{asset_name(symbol, size, off)}",
        }
        if action == "STATEFUL_SYMBOL":
            wanted.add(f"{family}/{asset_name(symbol, size, on)}")
        by_symbol.setdefault(symbol, set()).update(wanted)

    capability_rows = []
    failures = []
    for symbol in sorted(by_symbol):
        tree = api_get(
            f"/repos/{repo}/git/trees/{symbols[symbol]}?recursive=1",
            token,
        )
        if tree.get("truncated"):
            failures.append(f"{symbol}: subtree truncated")
            continue
        paths = {item["path"] for item in tree.get("tree", []) if item.get("type") == "blob"}
        for wanted in sorted(by_symbol[symbol]):
            exists = wanted in paths
            capability_rows.append([symbol, wanted, "1" if exists else "0"])
            if not exists:
                failures.append(f"{symbol}: missing {wanted}")

    with args.capabilities_output.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["symbol", "asset", "exists"])
        w.writerows(capability_rows)

    print(f"pinned_commit={actual}")
    print(f"symbol_directories={len(symbols)}")
    print(f"mapped_rows={len(rows)}")
    print(f"mapped_symbols={len(by_symbol)}")
    print(f"asset_checks={len(capability_rows)}")
    if failures:
        print("failures:")
        for failure in failures:
            print(" -", failure)
        return 1
    print("VERIFIED: all mapped Material Symbol assets exist at the pinned upstream commit")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
