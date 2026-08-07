#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import argparse
import hashlib
import shutil
import stat
import tempfile
import zipfile
from pathlib import Path

EXECUTABLES = {
    "customize.sh",
    "service.sh",
    "post-fs-data.sh",
    "action.sh",
    "uninstall.sh",
    "bin/monetctl",
    "META-INF/com/google/android/update-binary",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--components", type=Path, default=Path("build/components"))
    parser.add_argument("--frontend-apk", type=Path)
    parser.add_argument("--version", required=True)
    parser.add_argument("--version-code", required=True, type=int)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    root = args.root.resolve()
    runtime = args.runtime.resolve()
    components = (
        (root / args.components).resolve()
        if not args.components.is_absolute()
        else args.components.resolve()
    )
    frontend_apk = args.frontend_apk.resolve() if args.frontend_apk else None

    if not runtime.is_file():
        raise FileNotFoundError(runtime)
    if frontend_apk is not None and not frontend_apk.is_file():
        raise FileNotFoundError(frontend_apk)

    packages = sorted(components.glob("*.cmonet"))
    if not packages:
        raise RuntimeError("no .cmonet components")

    with tempfile.TemporaryDirectory(prefix="coloros-monet-v2-") as temp_dir:
        stage = Path(temp_dir) / "module"
        shutil.copytree(root / "module", stage)

        prop = (stage / "module.prop.in").read_text(encoding="utf-8")
        prop = prop.replace("@VERSION@", args.version).replace(
            "@VERSION_CODE@", str(args.version_code)
        )
        (stage / "module.prop").write_text(prop, encoding="utf-8")
        (stage / "module.prop.in").unlink()

        (stage / "bin").mkdir(exist_ok=True)
        shutil.copy2(runtime, stage / "bin/monetctl")

        destination = stage / "components"
        destination.mkdir(exist_ok=True)
        for package in packages:
            shutil.copy2(package, destination / package.name)

        # The public repository remains binary-clean. A user-supplied COE APK can
        # be injected only at packaging time for private/device-integration builds.
        if frontend_apk is not None:
            frontend_dir = stage / "frontend"
            frontend_dir.mkdir(exist_ok=True)
            target = frontend_dir / "COE-2.5.apk"
            shutil.copy2(frontend_apk, target)
            digest = sha256_file(target)
            (frontend_dir / "COE-2.5.apk.sha256").write_text(
                f"{digest}  COE-2.5.apk\n", encoding="utf-8"
            )
            (frontend_dir / "README.txt").write_text(
                "COE frontend bundle\n"
                "Package: one.dot.couiexpressive\n"
                "Settings activity: one.dot.couiexpressive.ui.SettingsActivity\n"
                "Role: user-facing frontend / LSPosed interaction layer\n"
                "Backend companion: ColorOS Monet Rust + CMONET01 runtime\n"
                "This APK is injected from a user-supplied local file and is not "
                "stored in the public repository.\n",
                encoding="utf-8",
            )

        # Do not ship obsolete static RRO payloads.
        shutil.rmtree(stage / "payload", ignore_errors=True)

        args.output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(
            args.output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as archive:
            for path in sorted(stage.rglob("*")):
                if not path.is_file():
                    continue
                relative = path.relative_to(stage).as_posix()
                info = zipfile.ZipInfo(relative)
                info.date_time = (2026, 1, 1, 0, 0, 0)
                mode = 0o755 if relative in EXECUTABLES else 0o644
                info.external_attr = (stat.S_IFREG | mode) << 16
                archive.writestr(
                    info,
                    path.read_bytes(),
                    compress_type=zipfile.ZIP_DEFLATED,
                    compresslevel=9,
                )

    suffix = " + COE frontend" if frontend_apk is not None else ""
    print(f"packed {len(packages)} components{suffix} -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
