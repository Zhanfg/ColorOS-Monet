#!/usr/bin/env python3
"""Classify a legacy resource-only overlay set against a local ColorOS target dump.

This tool contains no vendor resources. It consumes user-supplied APK/RRO files
locally and emits only compatibility metadata.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

RESOURCE_RE = re.compile(r"^\s*resource\s+0x[0-9a-fA-F]+\s+([^/\s]+)/(.+?)\s*$")
PACKAGE_RE = re.compile(r"package: name='([^']+)'")
TARGET_RE = re.compile(r"overlay: targetPackage='([^']+)'")

@dataclass(frozen=True)
class Row:
    overlay_apk: str
    overlay_package: str
    target_package: str
    resource_type: str
    resource_name: str
    category: str
    action: str
    target_present: bool

def run(*args: object) -> str:
    return subprocess.run(
        [str(x) for x in args],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=True,
    ).stdout

def badging(aapt2: Path, apk: Path) -> tuple[str, str]:
    out = run(aapt2, "dump", "badging", apk)
    package = PACKAGE_RE.search(out)
    target = TARGET_RE.search(out)
    return (
        package.group(1) if package else "",
        target.group(1) if target else "",
    )

def resource_names(aapt2: Path, apk: Path) -> set[tuple[str, str]]:
    proc = subprocess.Popen(
        [str(aapt2), "dump", "resources", "--no-values", str(apk)],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        bufsize=1,
    )
    result: set[tuple[str, str]] = set()
    assert proc.stdout is not None
    for line in proc.stdout:
        match = RESOURCE_RE.match(line)
        if not match:
            continue
        name = match.group(2)
        if name.endswith(" PUBLIC"):
            name = name[:-7]
        result.add((match.group(1), name))
    if proc.wait() != 0:
        raise RuntimeError(f"aapt2 resource dump failed: {apk}")
    return result

def classify(resource_type: str, name: str) -> str:
    n = name.lower()
    if resource_type in {"anim", "animator", "interpolator", "transition"} or any(
        x in n for x in ("animation", "animator", "interpolator", "motion", "transition")
    ):
        return "motion"
    if resource_type == "font" or any(
        x in n for x in ("font", "text_size", "textsize", "line_height", "letter_spacing", "typeface")
    ):
        return "typography"
    if "blur" in n:
        return "blur"
    if resource_type == "dimen":
        geometry = (
            "corner", "radius", "round", "padding", "margin", "height", "width",
            "size", "inset", "offset", "elevation", "divider", "spacing", "gap",
            "stroke", "thickness",
        )
        return "geometry" if any(x in n for x in geometry) else "dimension_other"
    if resource_type == "color":
        if any(x in n for x in ("divider", "separator", "outline", "border", "stroke")):
            return "divider_outline"
        if any(x in n for x in (
            "pressed", "press", "ripple", "disabled", "enabled", "selected",
            "checked", "unchecked", "focused", "hover", "highlight", "state_layer", "state",
        )):
            return "state_color"
        if any(x in n for x in (
            "background", "_bg", "surface", "card", "panel", "dialog", "popup",
            "sheet", "container", "neutral", "scrim", "shadow",
        )):
            return "surface_color"
        if any(x in n for x in ("text", "label", "icon", "foreground", "tint", "content", "on_")):
            return "content_color"
        if any(x in n for x in (
            "accent", "activated", "primary", "secondary", "tertiary", "link",
            "blue", "cyan", "green", "orange", "pink", "purple", "red", "yellow",
            "monet", "dynamic",
        )):
            return "semantic_accent"
        return "color_other"
    if resource_type in {"drawable", "mipmap"}:
        component = (
            "background", "_bg", "card", "shape", "selector", "ripple", "divider",
            "mask", "scrim", "panel", "dialog", "popup", "sheet", "tile", "switch",
            "radio", "checkbox", "button", "btn", "progress", "track", "thumb",
        )
        if any(x in n for x in component):
            return "component_drawable"
        if any(x in n for x in ("icon", "_ic", "ic_", "glyph", "logo")):
            return "icon_artwork"
        return "drawable_other"
    if resource_type in {"bool", "integer", "fraction", "string", "array", "plurals", "style", "attr"}:
        return "behavior_or_contract"
    return "other"

def policy_action(category: str, present: bool) -> str:
    if not present:
        if category in {
            "icon_artwork", "component_drawable", "drawable_other",
            "semantic_accent", "content_color",
        }:
            return "MIGRATE_RENAMED_OR_DROP"
        return "DROP_REMOVED_RESOURCE"
    if category in {
        "geometry", "dimension_other", "divider_outline", "surface_color",
        "state_color", "blur", "typography", "motion", "behavior_or_contract",
        "component_drawable",
    }:
        return "RESTORE_NATIVE"
    if category == "semantic_accent":
        return "MD3E_SEMANTIC"
    if category == "icon_artwork":
        return "PRESERVE_TARGET_GEOMETRY_TINT_ONLY"
    if category == "content_color":
        return "MD3E_CONTENT_OR_NATIVE"
    return "REVIEW"

def compact_target(target_dir: Path, output: Path) -> None:
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.write(target_dir / "AndroidManifest.xml", "AndroidManifest.xml")
        arsc = target_dir / "resources.arsc"
        if arsc.is_file():
            archive.write(arsc, "resources.arsc")

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--aapt2", type=Path, required=True)
    p.add_argument("--legacy-overlay-dir", type=Path, required=True)
    p.add_argument("--target-dump-dir", type=Path, required=True,
                   help="Directory containing compact target folders with AndroidManifest.xml/resources.arsc")
    p.add_argument("--output-dir", type=Path, required=True)
    args = p.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    legacy: list[tuple[Path, str, str, set[tuple[str, str]]]] = []
    wanted_targets: set[str] = set()
    for apk in sorted(args.legacy_overlay_dir.glob("*.apk")):
        package, target = badging(args.aapt2, apk)
        names = resource_names(args.aapt2, apk)
        legacy.append((apk, package, target, names))
        wanted_targets.add(target)

    with tempfile.TemporaryDirectory(prefix="coloros17-resource-classifier-") as td:
        temp = Path(td)
        targets: dict[str, set[tuple[str, str]]] = {}
        for directory in sorted(args.target_dump_dir.iterdir()):
            if not directory.is_dir() or not (directory / "AndroidManifest.xml").is_file():
                continue
            apk = temp / f"{directory.name}.apk"
            compact_target(directory, apk)
            package, _ = badging(args.aapt2, apk)
            if package in wanted_targets:
                targets[package] = resource_names(args.aapt2, apk)

        rows: list[Row] = []
        summaries: list[dict[str, object]] = []
        for apk, package, target, old_names in legacy:
            target_names = targets.get(target, set())
            actions: Counter[str] = Counter()
            present_count = 0
            for resource_type, name in sorted(old_names):
                present = (resource_type, name) in target_names
                present_count += int(present)
                category = classify(resource_type, name)
                action = policy_action(category, present)
                actions[action] += 1
                rows.append(Row(
                    apk.name, package, target, resource_type, name,
                    category, action, present,
                ))
            summaries.append({
                "overlay_apk": apk.name,
                "overlay_package": package,
                "target_package": target,
                "resource_count": len(old_names),
                "target_present_count": present_count,
                "target_missing_count": len(old_names) - present_count,
                "target_captured": target in targets,
                "actions": dict(actions),
            })

    with (args.output_dir / "legacy_resource_classification.tsv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(Row.__annotations__.keys())
        for row in rows:
            writer.writerow(asdict(row).values())

    (args.output_dir / "summary.json").write_text(
        json.dumps(summaries, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    totals = Counter(row.action for row in rows)
    lines = [
        "# ColorOS 17 legacy overlay classification",
        "",
        f"- Legacy overlays: **{len(summaries)}**",
        f"- Resource entries: **{len(rows)}**",
        "",
        "## Decisions",
        "",
    ]
    lines.extend(f"- `{name}`: **{count}**" for name, count in totals.most_common())
    lines.extend([
        "",
        "## Policy",
        "",
        "- Geometry/dividers/blur/neutral surfaces/state/typography/motion default to ColorOS 17.",
        "- Accent-semantic colors remain eligible for the native Monet/MD3E palette.",
        "- Vendor icon geometry stays native; only tint is eligible.",
        "- Removed/renamed legacy resources require an explicit migration or are dropped.",
        "- Ambiguous resources remain review items rather than receiving a package-wide rule.",
        "",
    ])
    (args.output_dir / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
