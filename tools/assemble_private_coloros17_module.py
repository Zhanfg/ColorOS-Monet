#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import shutil
import tempfile
import zipfile
from pathlib import Path

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def replace_prop(text: str, key: str, value: str) -> str:
    lines = text.splitlines()
    prefix = key + "="
    for i, line in enumerate(lines):
        if line.startswith(prefix):
            lines[i] = prefix + value
            break
    else:
        lines.append(prefix + value)
    return "\n".join(lines) + "\n"

def inject_preflight(customize: str) -> str:
    marker = "# COS17_NATIVEFIRST_PREFLIGHT"
    if marker in customize:
        return customize
    block = r'''
# COS17_NATIVEFIRST_PREFLIGHT
SDK="$(getprop ro.build.version.sdk 2>/dev/null)"
DISPLAY="$(getprop ro.build.display.id 2>/dev/null)"
OPLUSROM="$(getprop ro.build.version.oplusrom 2>/dev/null)"
case "$SDK" in
    37) ;;
    *)
        echo "[!] 本构建仅适用于 Android 17 / SDK 37 的 ColorOS 17"
        exit 1
        ;;
esac
case "$DISPLAY $OPLUSROM" in
    *17.0*|*ColorOS*17*|*OxygenOS*17*) ;;
    *)
        echo "[!] 未确认 ColorOS/OxygenOS 17 构建，停止安装"
        exit 1
        ;;
esac
echo "[#] ColorOS 17 native-first + MD3E compatibility active"
'''
    if customize.startswith("#!"):
        first, rest = customize.split("\n", 1)
        return first + "\n" + block + "\n" + rest
    return block + "\n" + customize

def main() -> int:
    p = argparse.ArgumentParser(
        description="Assemble a private ColorOS 17 v0.2.0 module from a user-supplied legacy module plus clean-room native foundation overlays."
    )
    p.add_argument("--base-module", type=Path, required=True)
    p.add_argument("--native-foundation-dir", type=Path, required=True)
    p.add_argument("--settings-exact-overlay", type=Path)
    p.add_argument("--version", default="v0.2.0-alpha2")
    p.add_argument("--version-code", default="26100321")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()

    base = args.base_module.resolve()
    native = args.native_foundation_dir.resolve()
    exact = args.settings_exact_overlay.resolve() if args.settings_exact_overlay else None

    if not base.is_file():
        raise RuntimeError(f"missing base module: {base}")
    manifest = native / "native-foundation-manifest.tsv"
    if not manifest.is_file():
        raise RuntimeError(f"missing native foundation manifest: {manifest}")

    with tempfile.TemporaryDirectory(prefix="cos17-md3e-private-") as td:
        stage = Path(td) / "stage"
        stage.mkdir()
        with zipfile.ZipFile(base) as zf:
            zf.extractall(stage)

        prop_path = stage / "module.prop"
        customize_path = stage / "customize.sh"
        overlay_dir = stage / "system/product/overlay"
        if not prop_path.is_file() or not customize_path.is_file() or not overlay_dir.is_dir():
            raise RuntimeError("base module is missing module.prop/customize.sh/system/product/overlay")

        # Preserve the user's complete legacy overlay set, then add only
        # higher-priority ColorOS 17 correction layers.
        copied = []
        for apk in sorted(native.glob("*.apk")):
            dst = overlay_dir / apk.name
            shutil.copy2(apk, dst)
            copied.append(dst.name)

        if exact:
            if not exact.is_file():
                raise RuntimeError(f"missing settings exact overlay: {exact}")
            dst = overlay_dir / "COS17_settings_extra_exact.apk"
            shutil.copy2(exact, dst)
            copied.append(dst.name)

        prop = prop_path.read_text(encoding="utf-8")
        prop = replace_prop(prop, "name", "Material You / MD3E for ColorOS 17")
        prop = replace_prop(prop, "version", args.version)
        prop = replace_prop(prop, "versionCode", str(args.version_code))
        prop = replace_prop(
            prop,
            "description",
            "ColorOS 17 native-first Monet/MD3E: preserves OEM geometry, blur and grouped-list semantics while adding scoped dynamic-color enhancements.",
        )
        prop_path.write_text(prop, encoding="utf-8")

        customize = customize_path.read_text(encoding="utf-8")
        customize_path.write_text(inject_preflight(customize), encoding="utf-8")

        compat = stage / "compat"
        compat.mkdir(exist_ok=True)
        rows = [
            "ColorOS 17 native-first private fusion build",
            f"base_module={base.name}",
            f"base_sha256={sha256(base)}",
            f"version={args.version}",
            f"version_code={args.version_code}",
            "",
            "added_overlays:",
            *[f"- {name}" for name in copied],
            "",
            "design_policy:",
            "- preserve legacy broad package coverage",
            "- restore ColorOS 17 native shared geometry/surface tokens at higher RRO priority",
            "- preserve exact ColorOS 17 Settings icon geometry",
            "- avoid generic redrawn vendor icons",
            "- COE package-wide CardHook/ListHook is handled separately",
        ]
        (compat / "COLOROS17_MD3E_FUSION.txt").write_text("\n".join(rows) + "\n", encoding="utf-8")

        args.output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(args.output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            for path in sorted(stage.rglob("*")):
                if path.is_file():
                    zf.write(path, path.relative_to(stage).as_posix())

    print(args.output)
    print("sha256", sha256(args.output))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
