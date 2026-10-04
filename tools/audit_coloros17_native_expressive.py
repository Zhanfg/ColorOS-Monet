#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
import subprocess
import tempfile
import zipfile
from collections import Counter
from pathlib import Path

PACKAGE_RE = re.compile(r"package: name='([^']+)'")
RESOURCE_RE = re.compile(r"^\s*resource\s+0x[0-9a-fA-F]+\s+([^/\s]+)/(.+?)\s*$")

def run(*args: object) -> str:
    return subprocess.run(
        [str(x) for x in args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    ).stdout

def compact_apk(source: Path, output: Path) -> None:
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as z:
        z.write(source / "AndroidManifest.xml", "AndroidManifest.xml")
        z.write(source / "resources.arsc", "resources.arsc")

def category(name: str) -> str:
    n = name.lower()
    if n.startswith("$"):
        return "GENERATED_FRAME"
    if "anim" in n:
        return "ANIMATION"
    if "icon" in n or n.startswith("ic_"):
        return "ICON"
    if any(x in n for x in ("background", "_bg", "card", "button", "switch", "spinner")):
        return "COMPONENT_SURFACE"
    return "OTHER"

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--aapt2", type=Path, required=True)
    p.add_argument("--targets", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()

    rows = []
    with tempfile.TemporaryDirectory(prefix="cos17-expressive-") as td:
        temp = Path(td)
        for source in sorted(x for x in args.targets.iterdir() if x.is_dir()):
            manifest = source / "AndroidManifest.xml"
            arsc = source / "resources.arsc"
            if not manifest.is_file() or not arsc.is_file():
                continue

            apk = temp / f"{source.name}.apk"
            compact_apk(source, apk)
            badging = run(args.aapt2, "dump", "badging", apk)
            match = PACKAGE_RE.search(badging)
            package = match.group(1) if match else ""

            resources = run(args.aapt2, "dump", "resources", "--no-values", apk)
            for line in resources.splitlines():
                match = RESOURCE_RE.match(line)
                if not match:
                    continue
                resource_type, name = match.groups()
                name = name.removesuffix(" PUBLIC")
                if resource_type not in {"drawable", "mipmap"}:
                    continue
                if "expressive" not in name.lower():
                    continue
                rows.append({
                    "target_package": package,
                    "resource_type": resource_type,
                    "resource_name": name,
                    "category": category(name),
                    "source_target": source.name,
                })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "target_package",
        "resource_type",
        "resource_name",
        "category",
        "source_target",
    ]
    with args.output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    print(f"expressive_resources={len(rows)}")
    for key, count in Counter(r["target_package"] for r in rows).most_common():
        print(f"package[{key}]={count}")
    for key, count in Counter(r["category"] for r in rows).most_common():
        print(f"category[{key}]={count}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
