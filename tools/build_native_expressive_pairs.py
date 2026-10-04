#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
import subprocess
import tempfile
import zipfile
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
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.write(source / "AndroidManifest.xml", "AndroidManifest.xml")
        archive.write(source / "resources.arsc", "resources.arsc")

def base_candidates(name: str) -> list[str]:
    candidates = {
        name.replace("_expressive", ""),
        name.replace("expressive_", ""),
        name.replace("_expressive_", "_"),
    }
    if name.startswith("settingslib_expressive_"):
        candidates.add(name.replace("settingslib_expressive_", "settingslib_", 1))
    if name.startswith("settings_expressive_"):
        candidates.add(name.replace("settings_expressive_", "settings_", 1))
    return sorted(x for x in candidates if x != name)

def classification(name: str) -> str:
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
    p.add_argument("--pairs", type=Path, required=True)
    p.add_argument("--unmatched", type=Path, required=True)
    args = p.parse_args()

    packages: dict[str, tuple[str, set[tuple[str, str]]]] = {}

    with tempfile.TemporaryDirectory(prefix="cos17-expressive-pairs-") as td:
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
            resources: set[tuple[str, str]] = set()
            for line in run(args.aapt2, "dump", "resources", "--no-values", apk).splitlines():
                match = RESOURCE_RE.match(line)
                if not match:
                    continue
                typ, name = match.groups()
                resources.add((typ, name.removesuffix(" PUBLIC")))
            packages[package] = (source.name, resources)

    pairs = []
    unmatched = []
    for package, (source_name, resources) in packages.items():
        for typ, name in sorted(resources):
            if typ not in {"drawable", "mipmap"} or "expressive" not in name.lower():
                continue
            if name.startswith("$"):
                continue
            matches = [x for x in base_candidates(name) if (typ, x) in resources]
            if matches:
                for base in matches:
                    pairs.append(
                        (package, typ, base, name, "EXACT_SIBLING_NAME", source_name)
                    )
            else:
                unmatched.append(
                    (package, typ, name, classification(name), source_name)
                )

    args.pairs.parent.mkdir(parents=True, exist_ok=True)
    with args.pairs.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow([
            "target_package","resource_type","base_resource",
            "expressive_resource","evidence","source_target",
        ])
        writer.writerows(sorted(pairs))

    with args.unmatched.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow([
            "target_package","resource_type","expressive_resource",
            "classification","source_target",
        ])
        writer.writerows(sorted(unmatched))

    print(f"exact_sibling_pairs={len(pairs)}")
    print(f"unmatched_expressive_resources={len(unmatched)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
