#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
import shutil
import tempfile
import zipfile

OVERLAYS: dict[str, str] = {}


def find_apk(project: Path, variant: str) -> Path:
    candidates = sorted((project / "build" / "outputs" / "apk" / variant).glob("*.apk"))
    if len(candidates) != 1:
        raise RuntimeError(f"expected one {variant} APK under {project}, found {len(candidates)}")
    return candidates[0]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path.cwd())
    p.add_argument("--variant", choices=("debug", "release"), required=True)
    p.add_argument("--version", required=True)
    p.add_argument("--version-code", required=True, type=int)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--native-foundation-dir", type=Path)
    p.add_argument("--semantic-accent-dir", type=Path)
    args = p.parse_args()
    root = args.root.resolve()

    with tempfile.TemporaryDirectory(prefix="coloros-monet-") as td:
        stage = Path(td) / "module"
        shutil.copytree(root / "module", stage)
        prop = (stage / "module.prop.in").read_text(encoding="utf-8")
        prop = prop.replace("@VERSION@", args.version).replace("@VERSION_CODE@", str(args.version_code))
        (stage / "module.prop").write_text(prop, encoding="utf-8")
        (stage / "module.prop.in").unlink()
        dest = stage / "payload" / "overlays"
        dest.mkdir(parents=True, exist_ok=True)
        for project_name, out_name in OVERLAYS.items():
            src = find_apk(root / "overlays" / project_name, args.variant)
            shutil.copy2(src, dest / out_name)

        if args.native_foundation_dir:
            native_src = args.native_foundation_dir.resolve()
            manifest = native_src / "native-foundation-manifest.tsv"
            if not manifest.is_file():
                raise RuntimeError(f"missing native foundation manifest: {manifest}")
            native_dest = stage / "payload" / "native-foundation"
            native_dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(manifest, native_dest / manifest.name)
            shutil.copy2(manifest, stage / "payload" / "native-foundation-manifest.tsv")
            for apk in sorted(native_src.glob("*.apk")):
                shutil.copy2(apk, native_dest / apk.name)

        if args.semantic_accent_dir:
            semantic_src = args.semantic_accent_dir.resolve()
            manifest = semantic_src / "semantic-accent-manifest.tsv"
            if not manifest.is_file():
                raise RuntimeError(f"missing semantic accent manifest: {manifest}")
            semantic_dest = stage / "payload" / "semantic-accent"
            semantic_dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(manifest, semantic_dest / manifest.name)
            shutil.copy2(manifest, stage / "payload" / "semantic-accent-manifest.tsv")
            for apk in sorted(semantic_src.glob("*.apk")):
                shutil.copy2(apk, semantic_dest / apk.name)

        args.output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(args.output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            for path in sorted(stage.rglob("*")):
                if path.is_file():
                    zf.write(path, path.relative_to(stage).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
