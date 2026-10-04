#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import difflib
import re
from pathlib import Path

PREFIXES = ("menu_ic_", "affordance_", "icon_", "ic_")
SIZE_RE = re.compile(r"_(16|18|20|22|24|32|36|40|48)(dp|px)?$")
PRESENTATION_SUFFIXES = ("_black", "_white", "_dark", "_light", "_icon", "_ic")
STATE_SUFFIXES = ("_filled", "_pressed", "_normal", "_themed", "_disabled")

def strip_prefix(name: str) -> str:
    value = name.lower()
    for prefix in PREFIXES:
        if value.startswith(prefix):
            return value[len(prefix):]
    return value

def candidate_forms(name: str) -> list[tuple[str, str, str]]:
    """Return candidate semantic forms without erasing state too early.

    Example:
      ic_bluetooth_disabled
        -> bluetooth_disabled  (exact semantic form)
        -> bluetooth           (state-stripped fallback)

    This prevents a real upstream symbol such as bluetooth_disabled from being
    silently collapsed to bluetooth.
    """
    value = strip_prefix(name)
    forms: list[tuple[str, str, str]] = []

    def add(v: str, reason: str, state_hint: str = "") -> None:
        v = v.strip("_")
        if not v:
            return
        if any(existing[0] == v for existing in forms):
            return
        forms.append((v, reason, state_hint))

    add(value, "exact_core")

    current = SIZE_RE.sub("", value)
    if current != value:
        add(current, "strip_size")

    changed = True
    while changed:
        changed = False
        for suffix in PRESENTATION_SUFFIXES:
            if current.endswith(suffix):
                current = current[: -len(suffix)]
                add(current, "strip_presentation")
                changed = True
                break

    state_current = current
    changed = True
    while changed:
        changed = False
        for suffix in STATE_SUFFIXES:
            if state_current.endswith(suffix):
                state_hint = suffix[1:]
                state_current = state_current[: -len(suffix)]
                add(state_current, "strip_state", state_hint)
                changed = True
                break

    return forms

def read_aliases(path: Path) -> dict[str, tuple[str, str]]:
    aliases = {}
    with path.open(encoding="utf-8", newline="") as f:
        for raw in f:
            if not raw.strip() or raw.lstrip().startswith("#"):
                continue
            name, symbol, confidence, *_ = next(csv.reader([raw], delimiter="\t"))
            aliases[name] = (symbol, confidence)
    return aliases

def upstream_symbols_from_tree(root: Path) -> set[str]:
    android = root / "symbols" / "android"
    if not android.is_dir():
        raise RuntimeError(f"missing upstream symbols tree: {android}")
    return {p.name for p in android.iterdir() if p.is_dir()}

def upstream_symbols_from_catalog(path: Path) -> set[str]:
    symbols = set()
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        if not reader.fieldnames or "symbol" not in reader.fieldnames:
            raise RuntimeError(f"catalog lacks symbol column: {path}")
        for row in reader:
            if row.get("symbol"):
                symbols.add(row["symbol"])
    return symbols

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--inventory", type=Path, required=True)
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument("--upstream", type=Path)
    source.add_argument("--catalog", type=Path)
    p.add_argument("--aliases", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()

    symbols = (
        upstream_symbols_from_tree(args.upstream)
        if args.upstream
        else upstream_symbols_from_catalog(args.catalog)
    )
    aliases = read_aliases(args.aliases)
    sorted_symbols = sorted(symbols)
    rows = []

    with args.inventory.open(encoding="utf-8", newline="") as f:
        for item in csv.DictReader(f, delimiter="\t"):
            if item["classification"] != "GENERIC_CANDIDATE":
                continue

            forms = candidate_forms(item["resource_name"])
            candidates: list[tuple[str, float, str, str, str]] = []

            for rank, (form, reason, state_hint) in enumerate(forms):
                if form in symbols:
                    score = 1.0 - min(rank, 4) * 0.015
                    candidates.append((form, score, reason, form, state_hint))

                if form in aliases and aliases[form][0] in symbols:
                    alias_symbol, _alias_confidence = aliases[form]
                    score = 0.98 - min(rank, 4) * 0.015
                    candidates.append(
                        (alias_symbol, score, "curated_alias", form, state_hint)
                    )

            fuzzy_base = forms[0][0] if forms else item["resource_name"].lower()
            close = difflib.get_close_matches(
                fuzzy_base,
                sorted_symbols,
                n=5,
                cutoff=0.72,
            )
            for symbol in close:
                score = difflib.SequenceMatcher(None, fuzzy_base, symbol).ratio() * 0.90
                candidates.append(
                    (symbol, score, "fuzzy_name", fuzzy_base, "")
                )

            best: dict[str, tuple[float, str, str, str]] = {}
            for symbol, score, reason, normalized, state_hint in candidates:
                if symbol not in best or score > best[symbol][0]:
                    best[symbol] = (score, reason, normalized, state_hint)

            ranked = sorted(
                (
                    (symbol, score, reason, normalized, state_hint)
                    for symbol, (score, reason, normalized, state_hint)
                    in best.items()
                ),
                key=lambda x: (-x[1], x[0]),
            )[:3]

            out = dict(item)
            out["primary_form"] = forms[0][0] if forms else ""
            for i in range(3):
                if i < len(ranked):
                    symbol, score, reason, normalized, state_hint = ranked[i]
                    out[f"candidate_{i+1}"] = symbol
                    out[f"score_{i+1}"] = f"{score:.3f}"
                    out[f"reason_{i+1}"] = reason
                    out[f"matched_form_{i+1}"] = normalized
                    out[f"state_hint_{i+1}"] = state_hint
                else:
                    out[f"candidate_{i+1}"] = ""
                    out[f"score_{i+1}"] = ""
                    out[f"reason_{i+1}"] = ""
                    out[f"matched_form_{i+1}"] = ""
                    out[f"state_hint_{i+1}"] = ""
            rows.append(out)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else [
        "target_package","resource_type","resource_name","classification",
        "source_target","primary_form",
        "candidate_1","score_1","reason_1","matched_form_1","state_hint_1",
        "candidate_2","score_2","reason_2","matched_form_2","state_hint_2",
        "candidate_3","score_3","reason_3","matched_form_3","state_hint_3",
    ]
    with args.output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    exact = sum(
        1 for row in rows
        if row.get("reason_1") in {
            "exact_core", "strip_size", "strip_presentation",
            "strip_state", "curated_alias",
        }
    )
    print(f"candidate_rows={len(rows)}")
    print(f"deterministic_top1={exact}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
