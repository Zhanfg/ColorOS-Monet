#!/usr/bin/env python3
"""Build the ColorOS 17 Settings compatibility RRO and a systemless hotfix ZIP."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "overlays" / "coloros-settings17"
COMPILE_SDK_DIR = "37.0"


def run(*args: str | Path) -> None:
    command = [str(arg) for arg in args]
    print("+", " ".join(command))
    subprocess.run(command, check=True)


def sdk_tools() -> tuple[Path, Path, Path, Path]:
    raw = os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME")
    if not raw:
        raise RuntimeError("ANDROID_SDK_ROOT or ANDROID_HOME is required")
    sdk = Path(raw).expanduser().resolve()
    android_jar = sdk / "platforms" / f"android-{COMPILE_SDK_DIR}" / "android.jar"
    candidates = sorted(
        (path for path in (sdk / "build-tools").glob("37.*") if path.is_dir()),
        reverse=True,
    )
    if not candidates:
        raise RuntimeError("Android SDK Build-Tools 37.x is required")
    tools = candidates[0]
    aapt2, zipalign, apksigner = (tools / "aapt2", tools / "zipalign", tools / "apksigner")
    for path in (android_jar, aapt2, zipalign, apksigner):
        if not path.is_file():
            raise RuntimeError(f"missing SDK tool: {path}")
    return android_jar, aapt2, zipalign, apksigner


def debug_keystore() -> Path:
    key = ROOT / "build" / "signing" / "debug.keystore"
    if not key.is_file():
        key.parent.mkdir(parents=True, exist_ok=True)
        run(
            "keytool", "-genkeypair", "-noprompt",
            "-keystore", key, "-storepass", "android", "-keypass", "android",
            "-alias", "androiddebugkey",
            "-dname", "CN=Android Debug,O=Android,C=US",
            "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000",
        )
    return key


def build_apk(version: str, version_code: int) -> Path:
    android_jar, aapt2, zipalign, apksigner = sdk_tools()
    output_dir = PROJECT / "build" / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "ColorOSSettings17Compat.apk"
    manifest = PROJECT / "src" / "main" / "AndroidManifest.xml"
    res = PROJECT / "src" / "main" / "res"

    with tempfile.TemporaryDirectory(prefix="cos17-rro-") as raw:
        work = Path(raw)
        compiled = work / "compiled.zip"
        unsigned = work / "unsigned.apk"
        aligned = work / "aligned.apk"
        run(aapt2, "compile", "--dir", res, "-o", compiled)
        run(
            aapt2, "link",
            "-o", unsigned,
            "-I", android_jar,
            "--manifest", manifest,
            "--auto-add-overlay",
            "--min-sdk-version", "37",
            "--target-sdk-version", "37",
            "--version-code", str(version_code),
            "--version-name", version,
            compiled,
        )
        run(zipalign, "-f", "4", unsigned, aligned)
        key = debug_keystore()
        run(
            apksigner, "sign",
            "--ks", key, "--ks-pass", "pass:android",
            "--ks-key-alias", "androiddebugkey", "--key-pass", "pass:android",
            "--out", output, aligned,
        )
        run(apksigner, "verify", "--verbose", output)
    return output


def package_hotfix(apk: Path, output: Path, version: str, version_code: int) -> None:
    module_prop = f"""id=coloros_monet_cos17_settings_hotfix
name=ColorOS Monet - ColorOS 17 Settings Hotfix
version={version}
versionCode={version_code}
author=ColorOS-Monet contributors
description=Android 17 / ColorOS 17 Settings resource compatibility overlay. Clean-room artwork only.
"""
    customize = """#!/system/bin/sh
SDK="$(getprop ro.build.version.sdk 2>/dev/null)"
[ "$SDK" = 37 ] || abort "! This hotfix is only for Android 17 / SDK 37."
ui_print "- ColorOS 17 Settings Monet compatibility overlay"
ui_print "- No app/service restart is performed. Reboot after installation."
"""
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.writestr("module.prop", module_prop)
        zf.writestr("customize.sh", customize)
        zf.write(apk, "system/product/overlay/ColorOSSettings17Compat.apk")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="0.1.5-beta")
    parser.add_argument("--version-code", type=int, default=26100301)
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / "ColorOS-Monet-COS17-hotfix.zip")
    args = parser.parse_args()
    apk = build_apk(args.version, args.version_code)
    package_hotfix(apk, args.output, args.version, args.version_code)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
