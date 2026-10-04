#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAP = ROOT / "compat/coloros17/settings_oplus_homepage_icons.tsv"

def run(*args: object) -> None:
    cmd = [str(x) for x in args]
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)

def rows(path: Path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))

def drawable_name(value: str) -> str:
    value = value.strip()
    for prefix in ("drawable/", "@drawable/"):
        if value.startswith(prefix):
            return value[len(prefix):]
    return value

def build_alias_xml(mapping: Path) -> tuple[str, list[tuple[str, str, str]]]:
    selected = []
    for row in rows(mapping):
        if row["action"] != "NATIVE_EXPRESSIVE":
            continue
        source = drawable_name(row["current_icon"])
        target = drawable_name(row["candidate"])
        if not source or not target:
            raise RuntimeError(f"incomplete mapping row: {row}")
        selected.append((row["key"], source, target))

    if not selected:
        raise RuntimeError("no NATIVE_EXPRESSIVE rows selected")

    lines = ['<?xml version="1.0" encoding="utf-8"?>', "<resources>"]
    for _, source, target in selected:
        # '*' intentionally permits references to private resources in the
        # local target APK. No vendor asset is copied into this repository.
        lines.append(
            f'    <item type="drawable" name="{source}">'
            f'@*com.android.settings:drawable/{target}</item>'
        )
    lines.append("</resources>")
    return "\n".join(lines) + "\n", selected

def main() -> int:
    p = argparse.ArgumentParser(
        description=(
            "Build an experiment-only RRO that redirects selected OPlus Settings "
            "homepage glyph resources to native Expressive resources already "
            "present in the same Settings APK."
        )
    )
    p.add_argument("--aapt2", type=Path, required=True)
    p.add_argument("--framework-res", type=Path, required=True)
    p.add_argument("--settings-apk", type=Path, required=True)
    p.add_argument("--mapping", type=Path, default=DEFAULT_MAP)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--package", default="dev.zhanfg.coloros17.experiment.settingsicons")
    p.add_argument("--version-code", type=int, default=26100410)
    p.add_argument("--version-name", default="0.2.0-settings-icons-exp1")
    args = p.parse_args()

    aliases, selected = build_alias_xml(args.mapping)

    with tempfile.TemporaryDirectory(prefix="cos17-settings-icons-") as td:
        work = Path(td)
        values = work / "res" / "values"
        values.mkdir(parents=True)
        (values / "aliases.xml").write_text(aliases, encoding="utf-8")

        manifest = work / "AndroidManifest.xml"
        manifest.write_text(
            f'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="{args.package}"
    android:versionCode="{args.version_code}"
    android:versionName="{args.version_name}">
    <uses-sdk android:minSdkVersion="37" android:targetSdkVersion="37" />
    <application android:allowBackup="false" android:hasCode="false" />
    <overlay android:targetPackage="com.android.settings" android:isStatic="false" />
</manifest>
''',
            encoding="utf-8",
        )

        compiled = work / "compiled.zip"
        unsigned = work / "unsigned.apk"
        run(args.aapt2, "compile", "--dir", work / "res", "-o", compiled)
        run(
            args.aapt2,
            "link",
            "-o", unsigned,
            "-I", args.framework_res,
            "-I", args.settings_apk,
            "--manifest", manifest,
            "--auto-add-overlay",
            compiled,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(unsigned.read_bytes())

    print(f"built aliases={len(selected)} -> {args.output}")
    for key, source, target in selected:
        print(f"{key}: {source} -> {target}")
    print(
        "NOTE: experiment-only, unsigned. Runtime activation remains gated on "
        "OPlus visual verification and OverlayManager acceptance."
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
