#!/usr/bin/env python3
"""Build resource-only RRO APKs with Android SDK command-line tools."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
COMPILE_SDK = 35
BUILD_TOOLS_PREFERRED = "35.0.0"

OVERLAYS = {
    "coloros-settings": {"mapping": None},
    "x": {"mapping": "mapping/colors.tsv"},
    "tim": {"mapping": "mapping/colors.tsv"},
    "coolapk": {"mapping": "mapping"},
}


def run(*args: str | Path, env: dict[str, str] | None = None) -> None:
    command = [str(arg) for arg in args]
    print("+", " ".join(command))
    subprocess.run(command, check=True, env=env)


def version_key(path: Path) -> tuple[int, ...]:
    numbers = re.findall(r"\d+", path.name)
    return tuple(int(value) for value in numbers)


def find_sdk() -> tuple[Path, Path, Path, Path]:
    raw = os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME")
    if not raw:
        raise RuntimeError("ANDROID_SDK_ROOT or ANDROID_HOME is required")
    sdk = Path(raw).expanduser().resolve()
    android_jar = sdk / "platforms" / f"android-{COMPILE_SDK}" / "android.jar"
    build_tools_root = sdk / "build-tools"
    preferred = build_tools_root / BUILD_TOOLS_PREFERRED
    candidates = [preferred] if preferred.is_dir() else []
    candidates.extend(
        path for path in sorted(build_tools_root.glob("*"), key=version_key, reverse=True)
        if path.is_dir() and path != preferred
    )
    if not candidates:
        raise RuntimeError(f"no Android build-tools found under {build_tools_root}")
    tools = candidates[0]
    aapt2 = tools / "aapt2"
    zipalign = tools / "zipalign"
    apksigner = tools / "apksigner"
    for required in (android_jar, aapt2, zipalign, apksigner):
        if not required.is_file():
            raise RuntimeError(f"missing Android SDK tool: {required}")
    return android_jar, aapt2, zipalign, apksigner


def debug_keystore() -> tuple[Path, str, str, str]:
    keystore = ROOT / "build" / "signing" / "debug.keystore"
    if not keystore.is_file():
        keystore.parent.mkdir(parents=True, exist_ok=True)
        run(
            "keytool", "-genkeypair", "-noprompt",
            "-keystore", keystore,
            "-storepass", "android",
            "-keypass", "android",
            "-alias", "androiddebugkey",
            "-dname", "CN=Android Debug,O=Android,C=US",
            "-keyalg", "RSA",
            "-keysize", "2048",
            "-validity", "10000",
        )
    return keystore, "android", "androiddebugkey", "android"


def release_keystore() -> tuple[Path, str, str, str]:
    values = {
        "file": os.environ.get("MONET_KEYSTORE_FILE", ""),
        "store_password": os.environ.get("MONET_KEYSTORE_PASSWORD", ""),
        "alias": os.environ.get("MONET_KEY_ALIAS", ""),
        "key_password": os.environ.get("MONET_KEY_PASSWORD", ""),
    }
    missing = [name for name, value in values.items() if not value]
    if missing:
        raise RuntimeError(f"missing release signing values: {', '.join(missing)}")
    keystore = Path(values["file"]).expanduser().resolve()
    if not keystore.is_file():
        raise RuntimeError(f"release keystore not found: {keystore}")
    return keystore, values["store_password"], values["alias"], values["key_password"]


def merge_resources(project: Path, mapping: str | None, destination: Path) -> None:
    source = project / "src" / "main" / "res"
    if source.is_dir():
        shutil.copytree(source, destination, dirs_exist_ok=True)
    if mapping:
        generated = destination.parent / "generated"
        run(
            sys.executable,
            ROOT / "tools" / "generate_colors.py",
            "--mapping", project / mapping,
            "--output", generated,
        )
        shutil.copytree(generated, destination, dirs_exist_ok=True)
    if not destination.is_dir() or not any(destination.rglob("*")):
        raise RuntimeError(f"no resources found for {project.name}")


def build_one(
    name: str,
    mapping: str | None,
    variant: str,
    version_name: str,
    version_code: int,
    signing: tuple[Path, str, str, str],
    android_jar: Path,
    aapt2: Path,
    zipalign: Path,
    apksigner: Path,
) -> Path:
    project = ROOT / "overlays" / name
    manifest = project / "src" / "main" / "AndroidManifest.xml"
    if not manifest.is_file():
        raise RuntimeError(f"missing manifest: {manifest}")
    output_dir = project / "build" / "outputs" / "apk" / variant
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"{name}-{variant}.apk"

    with tempfile.TemporaryDirectory(prefix=f"rro-{name}-") as raw:
        work = Path(raw)
        merged = work / "res"
        merge_resources(project, mapping, merged)
        compiled = work / "compiled.zip"
        unsigned = work / "unsigned.apk"
        aligned = work / "aligned.apk"
        run(aapt2, "compile", "--dir", merged, "-o", compiled)
        run(
            aapt2, "link",
            "-o", unsigned,
            "-I", android_jar,
            "--manifest", manifest,
            "--auto-add-overlay",
            "--min-sdk-version", "31",
            "--target-sdk-version", str(COMPILE_SDK),
            "--version-code", str(version_code),
            "--version-name", version_name,
            compiled,
        )
        run(zipalign, "-f", "4", unsigned, aligned)
        keystore, store_password, alias, key_password = signing
        run(
            apksigner, "sign",
            "--ks", keystore,
            "--ks-pass", f"pass:{store_password}",
            "--ks-key-alias", alias,
            "--key-pass", f"pass:{key_password}",
            "--out", output,
            aligned,
        )
        run(apksigner, "verify", "--verbose", output)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", choices=("debug", "release"), required=True)
    parser.add_argument("--version-name", default="1.0.0")
    parser.add_argument("--version-code", type=int, default=1)
    args = parser.parse_args()
    try:
        android_jar, aapt2, zipalign, apksigner = find_sdk()
        signing = debug_keystore() if args.variant == "debug" else release_keystore()
        outputs = [
            build_one(
                name,
                config["mapping"],
                args.variant,
                args.version_name,
                args.version_code,
                signing,
                android_jar,
                aapt2,
                zipalign,
                apksigner,
            )
            for name, config in OVERLAYS.items()
        ]
        run(sys.executable, ROOT / "tools" / "audit_apks.py", *outputs)
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print("built overlays:")
    for output in outputs:
        print(output.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
