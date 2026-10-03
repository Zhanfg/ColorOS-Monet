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
SDK_DIR = "37.0"
BUILD_TOOLS = "37.0.0"
TABLES = [
    ROOT / "compat/coloros17/native_restore.tsv",
    ROOT / "compat/coloros17/native_surface_restore.tsv",
]

@dataclass(frozen=True)
class Entry:
    key: str
    target: str
    typ: str
    name: str
    default: str
    night: str
    fmt: str

def run(*args: object) -> None:
    cmd = [str(x) for x in args]
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)

def sdk_tools() -> tuple[Path, Path, Path, Path]:
    sdk = Path(os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME") or "/usr/local/lib/android/sdk")
    android_jar = sdk / "platforms" / f"android-{SDK_DIR}" / "android.jar"
    bt = sdk / "build-tools" / BUILD_TOOLS
    tools = (android_jar, bt / "aapt2", bt / "zipalign", bt / "apksigner")
    for p in tools:
        if not p.is_file():
            raise RuntimeError(f"missing Android build tool: {p}")
    return tools

def signing_key() -> Path:
    key = ROOT / "build/signing/debug.keystore"
    if key.is_file():
        return key
    key.parent.mkdir(parents=True, exist_ok=True)
    run(
        "keytool", "-genkeypair", "-noprompt",
        "-keystore", key,
        "-storepass", "android", "-keypass", "android",
        "-alias", "androiddebugkey",
        "-dname", "CN=ColorOS17 Native Foundation,O=ColorOS-Monet,C=US",
        "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000",
    )
    return key

def read_tables() -> list[Entry]:
    out: list[Entry] = []
    seen: set[tuple[str, str, str, str]] = set()
    for table in TABLES:
        with table.open(encoding="utf-8", newline="") as f:
            for raw in f:
                if not raw.strip() or raw.lstrip().startswith("#"):
                    continue
                row = next(csv.reader([raw], delimiter="\t"))
                while len(row) < 7:
                    row.append("")
                e = Entry(*row[:7])
                ident = (e.key, e.target, e.typ, e.name)
                if ident in seen:
                    raise RuntimeError(f"duplicate native token: {ident}")
                seen.add(ident)
                out.append(e)
    if not out:
        raise RuntimeError("native restore tables are empty")
    return out

def values_xml(entries: list[Entry], night: bool) -> str:
    lines = ['<?xml version="1.0" encoding="utf-8"?>', "<resources>"]
    for e in entries:
        value = e.night if night and e.night else e.default
        if not value:
            continue
        if e.typ == "color":
            lines.append(f'    <color name="{e.name}">{value}</color>')
        elif e.typ == "dimen" and e.fmt == "float":
            lines.append(f'    <item type="dimen" name="{e.name}" format="float">{value}</item>')
        elif e.typ == "dimen":
            lines.append(f'    <dimen name="{e.name}">{value}</dimen>')
        elif e.typ == "bool":
            lines.append(f'    <bool name="{e.name}">{value}</bool>')
        elif e.typ == "integer":
            lines.append(f'    <integer name="{e.name}">{value}</integer>')
        else:
            raise RuntimeError(f"unsupported type {e.typ}/{e.name}")
    lines.append("</resources>")
    return "\n".join(lines) + "\n"

def build_one(
    key: str,
    target: str,
    entries: list[Entry],
    out_apk: Path,
    version: str,
    version_code: int,
    android_jar: Path,
    aapt2: Path,
    zipalign: Path,
    apksigner: Path,
    keystore: Path,
) -> None:
    with tempfile.TemporaryDirectory(prefix=f"cos17-native-{key}-") as td:
        t = Path(td)
        res = t / "res"
        (res / "values").mkdir(parents=True)
        default_entries = [e for e in entries if e.default]
        night_entries = [e for e in entries if e.night]
        (res / "values" / "native_foundation.xml").write_text(
            values_xml(default_entries, False), encoding="utf-8"
        )
        if night_entries:
            (res / "values-night").mkdir(parents=True)
            (res / "values-night" / "native_foundation.xml").write_text(
                values_xml(night_entries, True), encoding="utf-8"
            )

        pkg = f"dev.zhanfg.colorosmonet.native.{key}"
        manifest = t / "AndroidManifest.xml"
        manifest.write_text(
            f'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="{pkg}"
    android:versionCode="{version_code}"
    android:versionName="{version}">
    <uses-sdk android:minSdkVersion="37" android:targetSdkVersion="37" />
    <application android:allowBackup="false" android:hasCode="false" android:extractNativeLibs="false" />
    <overlay android:targetPackage="{target}" android:isStatic="false" />
</manifest>
''',
            encoding="utf-8",
        )

        compiled = t / "compiled.zip"
        unsigned = t / "unsigned.apk"
        aligned = t / "aligned.apk"
        run(aapt2, "compile", "--dir", res, "-o", compiled)
        run(
            aapt2, "link",
            "-o", unsigned,
            "-I", android_jar,
            "--manifest", manifest,
            "--auto-add-overlay",
            "--min-sdk-version", "37",
            "--target-sdk-version", "37",
            compiled,
        )
        run(zipalign, "-f", "4", unsigned, aligned)
        run(
            apksigner, "sign",
            "--ks", keystore,
            "--ks-pass", "pass:android",
            "--ks-key-alias", "androiddebugkey",
            "--key-pass", "pass:android",
            "--out", out_apk,
            aligned,
        )
        run(apksigner, "verify", "--verbose", out_apk)

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--version", default="0.2.0-alpha1")
    p.add_argument("--version-code", type=int, default=26100320)
    p.add_argument("--output", type=Path, default=ROOT / "dist/ColorOS17-NativeFoundation-P0P1.zip")
    args = p.parse_args()

    entries = read_tables()
    groups: dict[tuple[str, str], list[Entry]] = defaultdict(list)
    for e in entries:
        groups[(e.key, e.target)].append(e)

    android_jar, aapt2, zipalign, apksigner = sdk_tools()
    keystore = signing_key()

    out_dir = ROOT / "dist/native-foundation"
    shutil.rmtree(out_dir, ignore_errors=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_rows = ["key\ttarget_package\toverlay_package\tapk\tentry_count"]
    for i, ((key, target), vals) in enumerate(sorted(groups.items()), 1):
        apk = out_dir / f"COS17_NativeFoundation_{key}.apk"
        build_one(
            key, target, vals, apk,
            args.version, args.version_code + i,
            android_jar, aapt2, zipalign, apksigner, keystore,
        )
        manifest_rows.append(
            f"{key}\t{target}\tdev.zhanfg.colorosmonet.native.{key}\t{apk.name}\t{len(vals)}"
        )

    (out_dir / "native-foundation-manifest.tsv").write_text(
        "\n".join(manifest_rows) + "\n", encoding="utf-8"
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for f in sorted(out_dir.iterdir()):
            zf.write(f, f.name)
    print(f"built {len(groups)} native foundation overlays -> {args.output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
