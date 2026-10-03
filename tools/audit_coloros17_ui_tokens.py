#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "compat/coloros17/md3e_policy.json"

RESOURCE_DECL_RE = re.compile(
    r"<(?P<tag>color|dimen|item)\\b[^>]*\\bname=[\"'](?P<name>[^\"']+)[\"']",
    re.IGNORECASE,
)

def resource_key(tag: str, name: str, text: str) -> str | None:
    tag = tag.lower()
    if tag in {"color", "dimen"}:
        return f"{tag}/{name}"
    if tag == "item":
        m = re.search(r"\\btype=[\"'](color|dimen)[\"']", text, re.IGNORECASE)
        if m:
            return f"{m.group(1).lower()}/{name}"
    return None

def scan_sources(paths: list[Path], forbidden: set[str], review_rx: list[re.Pattern[str]]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for base in paths:
        if not base.exists():
            continue
        files = [base] if base.is_file() else list(base.rglob("*.xml"))
        for f in files:
            try:
                text = f.read_text(encoding="utf-8")
            except Exception:
                continue
            for m in RESOURCE_DECL_RE.finditer(text):
                key = resource_key(m.group("tag"), m.group("name"), m.group(0))
                if not key:
                    continue
                rel = f.relative_to(ROOT) if f.is_relative_to(ROOT) else f
                if key in forbidden:
                    errors.append(f"{rel}: forbidden global override {key}")
                elif any(rx.search(key) for rx in review_rx):
                    warnings.append(f"{rel}: review component-scoped override {key}")
    return errors, warnings

def main() -> int:
    ap = argparse.ArgumentParser(description="Guard ColorOS 17 native-first MD3E token policy.")
    ap.add_argument("paths", nargs="*", type=Path, default=[ROOT / "overlays"])
    ap.add_argument("--strict-review", action="store_true", help="Treat review-required resources as errors.")
    args = ap.parse_args()

    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    forbidden = set(policy["forbidden_global_resource_overrides"])
    review_rx = [re.compile(p) for p in policy["review_required_resource_patterns"]]

    errors, warnings = scan_sources(args.paths, forbidden, review_rx)

    for line in warnings:
        print("WARN:", line)
    for line in errors:
        print("ERROR:", line, file=sys.stderr)

    if args.strict_review and warnings:
        errors.extend(warnings)

    if errors:
        print(f"ColorOS17 MD3E guard: FAIL ({len(errors)} blocking issue(s), {len(warnings)} review item(s))", file=sys.stderr)
        return 1

    print(f"ColorOS17 MD3E guard: PASS ({len(warnings)} review item(s))")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
