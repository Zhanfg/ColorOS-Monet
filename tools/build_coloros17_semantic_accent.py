#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import os
import shutil
import subprocess
import tempfile
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "compat/coloros17/md3e_semantic_accent.tsv"
SDK_DIR = "37.0"
BUILD_TOOLS = "37.0.0"

@dataclass(frozen=True)
class Entry:
    key: str
    target: str
    name: str
    light: str
    dark: str

def run(*args: object) -> None:
    cmd = [str(x) for x in args]
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)

def sdk_tools() -> tuple[Path, Path, Path, Path]:
    sdk = Path(os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME") or "/usr/local/lib/android/sdk")
    android_jar = sdk / "platforms" / f"android-{SDK_DIR}" / "android.jar"
    bt = sdk / "build-tools" / BUILD_TOOLS
    tools = (android_jar, bt / "aapt2", bt / "zipalign", bt / "apksigner")
    for tool in tools:
        if not tool.is_file():
            raise RuntimeError(f"missing Android build tool: {tool}")
    return tools

def debug_key() -> Path:
    key = ROOT / "build/signing/debug.keystore"
    if key.is_file():
        return key
    key.parent.mkdir(parents=True, exist_ok=True)
    run(
        "keytool", "-genkeypair", "-noprompt",
        "-keystore", key, "-storepass", "android", "-keypass", "android",
        "-alias", "androiddebugkey",
        "-dname", "CN=ColorOS17 Semantic Accent,O=ColorOS-Monet,C=US",
        "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000",
    )
    return key

def read_table() -> list[Entry]:
    rows: list[Entry] = []
    with TABLE.open(encoding="utf-8", newline="") as f:
        for raw in f:
            if not raw.strip() or raw.lstrip().startswith("#"):
                continue
            row = next(csv.reader([raw], delimiter="\t"))
            rows.append(Entry(*row[:5]))
    return rows

def values(entries: list[Entry], night: bool) -> str:
    lines = ['<?xml version="1.0" encoding="utf-8"?>', "<resources>"]
    for entry in entries:
        value = entry.dark if night else entry.light
        lines.append(f'    <color name="{entry.name}">{value}</color>')
    lines.append("</resources>")
    return "\n".join(lines) + "\n"

def build_one(
    key: str,
    target: str,
    entries: list[Entry],
    output: Path,
    version: str,
    version_code: int,
    android_jar: Path,
    aapt2: Path,
    zipalign: Path,
    apksigner: Path,
    keystore: Path,
) -> None:
    with tempfile.TemporaryDirectory(prefix=f"cos17-semantic-{key}-") as td:
        work = Path(td)
        res = work / "res"
        (res / "values").mkdir(parents=True)
        (res / "values-night").mkdir(parents=True)
        (res / "values" / "semantic_accent.xml").write_text(values(entries, False), encoding="utf-8")
        (res / "values-night" / "semantic_accent.xml").write_text(values(entries, True), encoding="utf-8")

        package = f"dev.zhanfg.colorosmonet.semantic.{key}"
        manifest = work / "AndroidManifest.xml"
        manifest.write_text(
            f'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="{package}"
    android:versionCode="{version_code}"
    android:versionName="{version}">
    <uses-sdk android:minSdkVersion="37" android:targetSdkVersion="37" />
    <application android:allowBackup="false" android:hasCode="false" android:extractNativeLibs="false" />
    <overlay android:targetPackage="{target}" android:isStatic="false" />
</manifest>
''',
            encoding="utf-8",
        )

        compiled = work / "compiled.zip"
        unsigned = work / "unsigned.apk"
        aligned = work / "aligned.apk"
        run(aapt2, "compile", "--dir", res, "-o", compiled)
        run(
            aapt2, "link", "-o", unsigned, "-I", android_jar,
            "--manifest", manifest, "--auto-add-overlay",
            "--min-sdk-version", "37", "--target-sdk-version", "37", compiled,
        )
        run(zipalign, "-f", "4", unsigned, aligned)
        run(
            apksigner, "sign",
            "--ks", keystore, "--ks-pass", "pass:android",
            "--ks-key-alias", "androiddebugkey", "--key-pass", "pass:android",
            "--out", output, aligned,
        )
        run(apksigner, "verify", "--verbose", output)

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--version", default="0.2.0-alpha2")
    p.add_argument("--version-code", type=int, default=26100330)
    p.add_argument("--output", type=Path, default=ROOT / "dist/ColorOS17-MD3E-SemanticAccent.zip")
    args = p.parse_args()

    groups: dict[tuple[str, str], list[Entry]] = defaultdict(list)
    for entry in read_table():
        groups[(entry.key, entry.target)].append(entry)

    android_jar, aapt2, zipalign, apksigner = sdk_tools()
    keystore = debug_key()
    out_dir = ROOT / "dist/semantic-accent"
    shutil.rmtree(out_dir, ignore_errors=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_rows = ["key\ttarget_package\toverlay_package\tapk\tentry_count"]
    for index, ((key, target), entries) in enumerate(sorted(groups.items()), 1):
        apk = out_dir / f"COS17_MD3E_Semantic_{key}.apk"
        build_one(
            key, target, entries, apk,
            args.version, args.version_code + index,
            android_jar, aapt2, zipalign, apksigner, keystore,
        )
        manifest_rows.append(
            f"{key}\t{target}\tdev.zhanfg.colorosmonet.semantic.{key}\t{apk.name}\t{len(entries)}"
        )

    (out_dir / "semantic-accent-manifest.tsv").write_text(
        "\n".join(manifest_rows) + "\n", encoding="utf-8"
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for file in sorted(out_dir.iterdir()):
            zf.write(file, file.name)
    print(f"built {len(groups)} semantic accent overlays -> {args.output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
