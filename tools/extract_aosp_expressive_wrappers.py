#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

ANDROID = "{http://schemas.android.com/apk/res/android}"

def res_name(value: str, expected_type: str) -> str:
    prefix = f"@{expected_type}/"
    return value[len(prefix):] if value.startswith(prefix) else value

def main() -> int:
    p = argparse.ArgumentParser(
        description="Extract Expressive TintDrawable wrappers and consumers from an AOSP Settings checkout."
    )
    p.add_argument("--settings-root", type=Path, required=True)
    p.add_argument("--wrappers-output", type=Path, required=True)
    p.add_argument("--consumers-output", type=Path, required=True)
    args = p.parse_args()

    res = args.settings_root / "res"
    if not res.is_dir():
        raise RuntimeError(f"missing Settings res directory: {res}")

    wrappers = []
    expressive_names = set()

    for xml in sorted(res.glob("drawable*/*.xml")):
        name = xml.stem
        if "expressive" not in name:
            continue
        expressive_names.add(name)
        try:
            root = ET.parse(xml).getroot()
        except ET.ParseError:
            continue

        root_name = root.tag.rsplit("}", 1)[-1]
        if not root_name.endswith("TintDrawable"):
            continue

        drawable = root.attrib.get(ANDROID + "drawable", "")
        tint = root.attrib.get(ANDROID + "tint", "")
        wrappers.append(
            [
                name,
                res_name(drawable, "drawable"),
                res_name(tint, "color"),
                str(xml.relative_to(args.settings_root)),
            ]
        )

    consumers = defaultdict(set)
    for xml in sorted(res.rglob("*.xml")):
        try:
            root = ET.parse(xml).getroot()
        except ET.ParseError:
            continue
        for elem in root.iter():
            for value in elem.attrib.values():
                if not value.startswith("@drawable/"):
                    continue
                target = value.split("/", 1)[1]
                if target in expressive_names:
                    consumers[target].add(str(xml.relative_to(args.settings_root)))

    args.wrappers_output.parent.mkdir(parents=True, exist_ok=True)
    with args.wrappers_output.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["expressive_resource", "wrapped_drawable", "tint_role", "source_xml"])
        w.writerows(wrappers)

    with args.consumers_output.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["expressive_resource", "consumer_xml"])
        for resource in sorted(consumers):
            for consumer in sorted(consumers[resource]):
                w.writerow([resource, consumer])

    print(f"expressive_named_resources={len(expressive_names)}")
    print(f"tint_wrappers={len(wrappers)}")
    print(f"consumer_edges={sum(len(v) for v in consumers.values())}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
