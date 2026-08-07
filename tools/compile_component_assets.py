#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Compile clean-room text XML assets into standalone Android binary XML.

Temporary APKs are build intermediates only. The shipped module contains no APK;
`.cmonet` packages carry the extracted binary XML files directly.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ANDROID_NS = "http://schemas.android.com/apk/res/android"
LOCAL_REF = re.compile(r"@(?!(?:android:|0x))([A-Za-z0-9_]+)/([^\"'\s<]+)")
LOCAL_ATTR = re.compile(r"\?(?!android:)(?:attr/)?[A-Za-z0-9_$.-]+")


def read_rows(path: Path) -> list[list[str]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        fields += [""] * (4 - len(fields))
        rows.append(fields[:4])
    return rows


def write_rows(path: Path, rows: list[list[str]]) -> None:
    lines = [
        "# type\tresource_name\tvalue\tconfiguration",
        "# Assets below are compiled binary XML extracted from temporary build APKs.",
    ]
    lines += ["\t".join(row) for row in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def direct_value(value: str) -> str | None:
    if value.startswith("argb:"):
        raw = value[5:]
        return "#" + raw
    if value.startswith("string:"):
        return value[7:]
    if value.startswith(("@android:", "#", "0x")):
        return value
    if re.fullmatch(r"-?[0-9]+(?:\.[0-9]+)?(?:dp|dip|sp|px|pt|in|mm)?", value):
        return value
    if value in {"true", "false"}:
        return value
    return None


def fallback_xml(resource_type: str, night: bool) -> str:
    primary = "@android:color/system_primary_dark" if night else "@android:color/system_primary_light"
    surface = "@android:color/system_surface_container_high_dark" if night else "@android:color/system_surface_container_high_light"
    if resource_type == "anim":
        return f'''<?xml version="1.0" encoding="utf-8"?>
<set xmlns:android="{ANDROID_NS}" android:ordering="together">
  <alpha android:duration="180" android:fromAlpha="0.0" android:toAlpha="1.0" />
</set>
'''
    if resource_type == "color":
        return f'''<?xml version="1.0" encoding="utf-8"?>
<selector xmlns:android="{ANDROID_NS}">
  <item android:state_enabled="false" android:color="{surface}" android:alpha="0.38" />
  <item android:color="{primary}" />
</selector>
'''
    return f'''<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="{ANDROID_NS}"
    android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
  <path android:fillColor="{primary}"
      android:pathData="M4,4h16v16h-16zM7,7v10h10v-10z" />
</vector>
'''


def preprocess_xml(
    text: str,
    resource_type: str,
    config: str,
    primitive: dict[tuple[str, str, str], str],
) -> str:
    night = "night" in config.split("-")
    try:
        ET.fromstring(text)
    except ET.ParseError:
        return fallback_xml(resource_type, night)

    failed = False

    def replace(match: re.Match[str]) -> str:
        nonlocal failed
        ref_type, ref_name = match.group(1), match.group(2)
        if ref_type not in {"color", "dimen", "bool", "integer", "string"}:
            failed = True
            return match.group(0)
        value = primitive.get((ref_type, ref_name, config))
        if value is None:
            value = primitive.get((ref_type, ref_name, ""))
        resolved = direct_value(value) if value is not None else None
        if resolved is None or resolved.startswith("file:"):
            failed = True
            return match.group(0)
        return resolved

    text = LOCAL_REF.sub(replace, text)
    if LOCAL_ATTR.search(text):
        failed = True
    if failed:
        return fallback_xml(resource_type, night)
    try:
        ET.fromstring(text)
    except ET.ParseError:
        return fallback_xml(resource_type, night)
    return text


def locate_android_jar(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.resolve()
    sdk = Path(__import__("os").environ.get("ANDROID_SDK_ROOT", ""))
    candidates = sorted((sdk / "platforms").glob("android-*/android.jar"))
    if not candidates:
        raise FileNotFoundError("android.jar not found; pass --android-jar")
    return candidates[-1]


def compile_one_component(
    source: Path,
    destination: Path,
    aapt2: Path,
    android_jar: Path,
) -> int:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)
    rows = read_rows(destination / "resources.tsv")
    primitive = {
        (rtype, name, config): value
        for rtype, name, value, config in rows
        if not value.startswith("file:")
    }
    file_rows = [row for row in rows if row[2].startswith("file:")]
    if not file_rows:
        return 0

    with tempfile.TemporaryDirectory(prefix=f"compile-{source.name}-") as td:
        work = Path(td)
        res = work / "res"
        mapping: dict[tuple[str, str, str], tuple[str, Path]] = {}
        for rtype, name, value, config in file_rows:
            if rtype not in {"drawable", "color", "anim", "mipmap"}:
                raise ValueError(f"{source.name}: unsupported file resource type {rtype}")
            input_path = destination / value[5:]
            text = input_path.read_text(encoding="utf-8")
            text = preprocess_xml(text, rtype, config, primitive)
            digest = hashlib.sha256(f"{rtype}\0{name}\0{config}".encode()).hexdigest()[:20]
            compiled_name = f"r_{digest}"
            directory = res / rtype
            directory.mkdir(parents=True, exist_ok=True)
            xml_path = directory / f"{compiled_name}.xml"
            xml_path.write_text(text, encoding="utf-8")
            mapping[(rtype, name, config)] = (compiled_name, xml_path)

        manifest = work / "AndroidManifest.xml"
        manifest.write_text(
            f'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="{ANDROID_NS}" package="cc.axymorrsen.colorosmonet.assetcompiler">
  <uses-sdk android:minSdkVersion="31" android:targetSdkVersion="35" />
  <application android:hasCode="false" />
</manifest>
''',
            encoding="utf-8",
        )
        compiled = work / "compiled.zip"
        output_apk = work / "assets.apk"
        subprocess.run([str(aapt2), "compile", "--dir", str(res), "-o", str(compiled)], check=True)
        subprocess.run(
            [
                str(aapt2), "link", "-o", str(output_apk),
                "--manifest", str(manifest), "-I", str(android_jar),
                "--min-sdk-version", "31", "--target-sdk-version", "35",
                str(compiled),
            ],
            check=True,
        )

        out_assets = destination / "compiled-assets"
        out_assets.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_apk) as archive:
            names = set(archive.namelist())
            for row in file_rows:
                rtype, name, _value, config = row
                compiled_name, _xml_path = mapping[(rtype, name, config)]
                entry = f"res/{rtype}/{compiled_name}.xml"
                if entry not in names:
                    matches = [candidate for candidate in names if candidate.endswith(f"/{compiled_name}.xml")]
                    if len(matches) != 1:
                        raise FileNotFoundError(f"compiled asset not found for {rtype}/{name}: {matches}")
                    entry = matches[0]
                data = archive.read(entry)
                if not data.startswith(b"\x03\x00\x08\x00"):
                    raise ValueError(f"{entry} is not Android binary XML")
                asset_identity = (name + "\0" + config).encode("utf-8")
                asset_digest = hashlib.sha256(asset_identity).hexdigest()[:20]
                file_name = f"{rtype}-{asset_digest}.xml"
                target = out_assets / file_name
                target.write_bytes(data)
                row[2] = "file:compiled-assets/" + file_name

    shutil.rmtree(destination / "assets", ignore_errors=True)
    write_rows(destination / "resources.tsv", rows)
    return len(file_rows)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--sources", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--aapt2", type=Path, required=True)
    p.add_argument("--android-jar", type=Path)
    args = p.parse_args()
    android_jar = locate_android_jar(args.android_jar)
    if args.output.exists():
        shutil.rmtree(args.output)
    args.output.mkdir(parents=True)
    total = 0
    count = 0
    for source in sorted(path for path in args.sources.iterdir() if path.is_dir()):
        if not (source / "component.json").is_file():
            continue
        total += compile_one_component(source, args.output / source.name, args.aapt2, android_jar)
        count += 1
    catalog = args.sources / "catalog.json"
    if catalog.is_file():
        shutil.copy2(catalog, args.output / "catalog.json")
    print(f"compiled {total} binary XML assets across {count} components")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
