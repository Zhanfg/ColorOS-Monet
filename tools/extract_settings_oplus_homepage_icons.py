#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
import subprocess
from pathlib import Path

ELEMENT_RE = re.compile(r"^(\s*)E: ([^ ]+)")
ATTR_RE = re.compile(r"^(\s*)A: .+?:([^:(]+)\([^)]*\)=(.*)$")
RESOURCE_RE = re.compile(r"^\s*resource\s+(0x[0-9a-fA-F]+)\s+([^/\s]+)/(.+?)\s*$")

def run(*args: object) -> str:
    return subprocess.run(
        [str(x) for x in args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    ).stdout

def raw_string(value: str) -> str:
    if value.startswith('"'):
        return value.split('"', 2)[1]
    return value

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--aapt2", type=Path, required=True)
    p.add_argument("--settings-apk", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()

    resources = {}
    for line in run(args.aapt2, "dump", "resources", "--no-values", args.settings_apk).splitlines():
        m = RESOURCE_RE.match(line)
        if not m:
            continue
        rid, typ, name = m.groups()
        resources[rid.lower()] = (typ, name.removesuffix(" PUBLIC"))

    xml = run(
        args.aapt2,
        "dump",
        "xmltree",
        "--file",
        "res/xml/top_level_settings_oplus.xml",
        args.settings_apk,
    )

    nodes = []
    current = None
    for line in xml.splitlines():
        e = ELEMENT_RE.match(line)
        if e:
            if current:
                nodes.append(current)
            current = {"class": e.group(2), "attrs": {}}
            continue
        a = ATTR_RE.match(line)
        if a and current:
            current["attrs"][a.group(2)] = a.group(3)
    if current:
        nodes.append(current)

    def resolve(value: str) -> str:
        if not value.startswith("@0x"):
            return raw_string(value)
        item = resources.get(value[1:].lower())
        return f"{item[0]}/{item[1]}" if item else value

    rows = []
    for node in nodes:
        attrs = node["attrs"]
        if "key" not in attrs or "icon" not in attrs:
            continue
        rows.append({
            "preference_key": raw_string(attrs["key"]),
            "view_class": node["class"],
            "icon_resource": resolve(attrs["icon"]).removeprefix("drawable/"),
            "show_two_tone": "1" if attrs.get("showTwoToneColor") == "true" else "0",
            "tint_icon_new": resolve(attrs.get("tintIconNew", "")),
            "tint_type": resolve(attrs.get("tintType", "")),
            "need_change_draw_type": attrs.get("needChangeDrawType", "false"),
            "layout_category": raw_string(attrs.get("layoutCategory", "")),
            "controller": raw_string(attrs.get("controller", "")),
            "fragment": raw_string(attrs.get("fragment", "")),
        })

    fields = [
        "preference_key","view_class","icon_resource","show_two_tone",
        "tint_icon_new","tint_type","need_change_draw_type",
        "layout_category","controller","fragment",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    two_tone = sum(r["show_two_tone"] == "1" for r in rows)
    changed = sum(r["need_change_draw_type"] == "true" for r in rows)
    expressive_names = sum("expressive" in r["icon_resource"].lower() for r in rows)
    print(f"homepage_icons={len(rows)}")
    print(f"show_two_tone={two_tone}")
    print(f"need_change_draw_type={changed}")
    print(f"explicit_expressive_icon_names={expressive_names}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
