#!/usr/bin/env python3
"""Verify the public ColorOS 17 semantic table against user-supplied local ROM data.

The repository does not contain vendor APKs. This verifier consumes:
- the legacy v0.1.4 overlay APK directory;
- the compact ColorOS 17 target-dump directory;
- the current ROM framework-res.apk.

It proves that each semantic mapping both existed in the legacy module and still
exists in the current target package, and that the legacy value resolved to
system_primary_light/system_primary_dark.
"""
from __future__ import annotations

import argparse
import csv
import re
import subprocess
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TABLE = ROOT / "compat/coloros17/md3e_semantic_accent.tsv"

PACKAGE_RE = re.compile(r"package: name='([^']+)'")
TARGET_RE = re.compile(r"overlay: targetPackage='([^']+)'")
RESOURCE_RE = re.compile(r"^\s*resource\s+(0x[0-9a-fA-F]+)\s+([^/\s]+)/(.+?)\s*$")
COLOR_RE = re.compile(r"^\s*resource\s+0x[0-9a-fA-F]+\s+color/(\S+)")
VALUE_RE = re.compile(r"^\s*\(([^)]*)\)\s+(@0x[0-9a-fA-F]+|#[0-9a-fA-F]+)")


def run(*args: object) -> str:
    return subprocess.run(
        [str(x) for x in args],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=True,
    ).stdout


def badging(aapt2: Path, apk: Path) -> tuple[str, str]:
    text = run(aapt2, "dump", "badging", apk)
    package = PACKAGE_RE.search(text)
    target = TARGET_RE.search(text)
    return (
        package.group(1) if package else "",
        target.group(1) if target else "",
    )


def resource_names(aapt2: Path, apk: Path) -> set[tuple[str, str]]:
    names: set[tuple[str, str]] = set()
    for line in run(aapt2, "dump", "resources", "--no-values", apk).splitlines():
        match = RESOURCE_RE.match(line)
        if not match:
            continue
        name = match.group(3)
        if name.endswith(" PUBLIC"):
            name = name[:-7]
        names.add((match.group(2), name))
    return names


def color_values(aapt2: Path, apk: Path) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    current = ""
    for line in run(aapt2, "dump", "resources", apk).splitlines():
        match = COLOR_RE.match(line)
        if match:
            current = match.group(1)
            result.setdefault(current, {})
            continue
        if not current:
            continue
        match = VALUE_RE.match(line)
        if match:
            result[current][match.group(1)] = match.group(2)
        elif line.strip().startswith("resource "):
            current = ""
    return result


def framework_color_id(aapt2: Path, framework: Path, name: str) -> str:
    wanted = f"color/{name}"
    for line in run(aapt2, "dump", "resources", "--no-values", framework).splitlines():
        match = RESOURCE_RE.match(line)
        if match and f"{match.group(2)}/{match.group(3).removesuffix(' PUBLIC')}" == wanted:
            return match.group(1).lower()
    raise RuntimeError(f"framework color not found: {wanted}")


def compact_target(directory: Path, output: Path) -> None:
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.write(directory / "AndroidManifest.xml", "AndroidManifest.xml")
        arsc = directory / "resources.arsc"
        if arsc.is_file():
            archive.write(arsc, "resources.arsc")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aapt2", type=Path, required=True)
    parser.add_argument("--legacy-overlay-dir", type=Path, required=True)
    parser.add_argument("--target-dump-dir", type=Path, required=True)
    parser.add_argument("--framework-res", type=Path, required=True)
    parser.add_argument("--table", type=Path, default=DEFAULT_TABLE)
    args = parser.parse_args()

    primary_light = "@" + framework_color_id(
        args.aapt2, args.framework_res, "system_primary_light"
    )
    primary_dark = "@" + framework_color_id(
        args.aapt2, args.framework_res, "system_primary_dark"
    )

    legacy: dict[str, list[tuple[str, dict[str, dict[str, str]]]]] = defaultdict(list)
    for apk in sorted(args.legacy_overlay_dir.glob("*.apk")):
        _, target = badging(args.aapt2, apk)
        legacy[target].append((apk.name, color_values(args.aapt2, apk)))

    target_names: dict[str, set[tuple[str, str]]] = {}
    with tempfile.TemporaryDirectory(prefix="cos17-semantic-verify-") as td:
        temp = Path(td)
        for directory in sorted(args.target_dump_dir.iterdir()):
            if not directory.is_dir() or not (directory / "AndroidManifest.xml").is_file():
                continue
            apk = temp / f"{directory.name}.apk"
            compact_target(directory, apk)
            try:
                package, _ = badging(args.aapt2, apk)
                target_names[package] = resource_names(args.aapt2, apk)
            except subprocess.CalledProcessError:
                continue

    rows = []
    with args.table.open(encoding="utf-8", newline="") as file:
        for raw in file:
            if not raw.strip() or raw.lstrip().startswith("#"):
                continue
            cols = next(csv.reader([raw], delimiter="\t"))
            if len(cols) != 5:
                raise RuntimeError(f"invalid semantic row: {raw.rstrip()}")
            rows.append(cols)

    failures = []
    proven = []
    for key, target, name, light, dark in rows:
        if ("color", name) not in target_names.get(target, set()):
            failures.append(f"{key}: target resource missing {target}:color/{name}")
            continue

        evidence = []
        for apk_name, values in legacy.get(target, []):
            item = values.get(name, {})
            if item.get("") == primary_light and item.get("night") == primary_dark:
                evidence.append(apk_name)

        if not evidence:
            failures.append(
                f"{key}: no legacy primary mapping for {target}:color/{name}"
            )
            continue

        if light != "@android:color/system_primary_light" or dark != "@android:color/system_primary_dark":
            failures.append(f"{key}: public table mapping differs for {target}:color/{name}")
            continue

        proven.append((key, target, name, ",".join(evidence)))

    print(f"framework primary ids: light={primary_light} dark={primary_dark}")
    print(f"semantic rows: {len(rows)}")
    print(f"proven rows: {len(proven)}")
    print(f"failures: {len(failures)}")
    if failures:
        for failure in failures:
            print("FAIL", failure)
        return 1

    packages = len({target for _, target, _, _ in proven})
    print(f"VERIFIED: {len(proven)}/{len(rows)} resources across {packages} packages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
