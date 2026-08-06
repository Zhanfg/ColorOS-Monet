#!/usr/bin/env python3
"""Generate day/night Android color resources from reviewed mapping metadata."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

RESOURCE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
ANDROID_COLOR_RE = re.compile(r"^@android:color/system_(?:accent[123]|neutral[12])_(?:0|10|50|100|200|300|400|500|600|700|800|900|1000)$")


def load_mapping(path: Path):
    rows = []
    seen = set()
    files = sorted(path.glob("*.tsv")) if path.is_dir() else [path]
    if not files:
        raise ValueError(f"{path}: no mapping files found")
    for current in files:
        for line_no, raw in enumerate(current.read_text(encoding="utf-8").splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) != 4:
                raise ValueError(f"{current}:{line_no}: expected 4 tab-separated columns")
            name, role, day, night = parts
            if not RESOURCE_RE.fullmatch(name):
                raise ValueError(f"{current}:{line_no}: invalid Android resource name: {name}")
            if name in seen:
                raise ValueError(f"{current}:{line_no}: duplicate resource name: {name}")
            if not ANDROID_COLOR_RE.fullmatch(day) or not ANDROID_COLOR_RE.fullmatch(night):
                raise ValueError(f"{current}:{line_no}: non-public or unsupported system color reference")
            seen.add(name)
            rows.append((name, role, day, night))
    if not rows:
        raise ValueError(f"{path}: mapping is empty")
    return rows


def write_values(path: Path, rows, value_index: int):
    resources = ET.Element("resources")
    resources.append(ET.Comment("Generated from reviewed TSV mappings; do not edit by hand."))
    for name, role, day, night in rows:
        resources.append(ET.Comment(f" role={role} "))
        node = ET.SubElement(resources, "color", {"name": name})
        node.text = (day, night)[value_index]
    tree = ET.ElementTree(resources)
    ET.indent(tree, space="    ")
    path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mapping", type=Path, required=True, help="TSV file or directory containing TSV parts")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        rows = load_mapping(args.mapping)
        write_values(args.output / "values" / "colors.xml", rows, 0)
        write_values(args.output / "values-night" / "colors.xml", rows, 1)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
