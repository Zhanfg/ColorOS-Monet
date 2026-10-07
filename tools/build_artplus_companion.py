#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "artplus-companion"
BUILD = APP / "build"
COMPILE_SDK = 35
BUILD_TOOLS = "35.0.0"


def run(*args: str | Path) -> None:
    cmd = [str(x) for x in args]
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def find_sdk() -> tuple[Path, Path, Path, Path, Path]:
    sdk_raw = os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME")
    if not sdk_raw:
        raise RuntimeError("ANDROID_SDK_ROOT or ANDROID_HOME is required")
    sdk = Path(sdk_raw)
    android_jar = sdk / "platforms" / f"android-{COMPILE_SDK}" / "android.jar"
    tools = sdk / "build-tools" / BUILD_TOOLS
    aapt2 = tools / "aapt2"
    d8 = tools / "d8"
    zipalign = tools / "zipalign"
    apksigner = tools / "apksigner"
    for p in (android_jar, aapt2, d8, zipalign, apksigner):
        if not p.is_file():
            raise RuntimeError(f"missing Android SDK tool: {p}")
    return android_jar, aapt2, d8, zipalign, apksigner


def debug_keystore() -> Path:
    ks = BUILD / "debug.keystore"
    if not ks.is_file():
        ks.parent.mkdir(parents=True, exist_ok=True)
        run(
            "keytool", "-genkeypair", "-noprompt",
            "-keystore", ks,
            "-storepass", "android",
            "-keypass", "android",
            "-alias", "androiddebugkey",
            "-dname", "CN=Android Debug,O=Android,C=US",
            "-keyalg", "RSA",
            "-keysize", "2048",
            "-validity", "10000",
        )
    return ks


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--variant", choices=("debug",), default="debug")
    args = p.parse_args()
    del args

    android_jar, aapt2, d8, zipalign, apksigner = find_sdk()
    out_dir = BUILD / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    output = out_dir / "ColorOS-ARTPlus-Auto-debug.apk"

    with tempfile.TemporaryDirectory(prefix="artplus-auto-") as raw:
        work = Path(raw)
        compiled_res = work / "compiled.zip"
        linked = work / "linked.apk"
        classes = work / "classes"
        classes.mkdir()
        classes_jar = work / "classes.jar"
        dex_dir = work / "dex"
        dex_dir.mkdir()
        merged = work / "with-dex.apk"
        aligned = work / "aligned.apk"

        run(aapt2, "compile", "--dir", APP / "src" / "main" / "res", "-o", compiled_res)
        run(
            aapt2, "link",
            "-o", linked,
            "-I", android_jar,
            "--manifest", APP / "src" / "main" / "AndroidManifest.xml",
            "--min-sdk-version", "26",
            "--target-sdk-version", "35",
            "--version-code", "1",
            "--version-name", "0.1.0-alpha1",
            compiled_res,
        )

        sources = sorted((APP / "src" / "main" / "java").rglob("*.java"))
        if not sources:
            raise RuntimeError("no Java sources found")
        run(
            "javac",
            "-source", "8",
            "-target", "8",
            "-encoding", "UTF-8",
            "-classpath", android_jar,
            "-d", classes,
            *sources,
        )
        run("jar", "cf", classes_jar, "-C", classes, ".")
        run(d8, "--min-api", "26", "--lib", android_jar, "--output", dex_dir, classes_jar)

        shutil.copy2(linked, merged)
        with zipfile.ZipFile(merged, "a", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(dex_dir / "classes.dex", "classes.dex")

        run(zipalign, "-f", "4", merged, aligned)
        ks = debug_keystore()
        run(
            apksigner, "sign",
            "--ks", ks,
            "--ks-pass", "pass:android",
            "--ks-key-alias", "androiddebugkey",
            "--key-pass", "pass:android",
            "--out", output,
            aligned,
        )
        run(apksigner, "verify", "--verbose", "--print-certs", output)

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
