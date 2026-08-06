#!/usr/bin/env python3
"""Verify that built overlay APKs are resource-only RRO packages."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
import zipfile


def audit(apk: Path) -> list[str]:
    errors: list[str] = []
    try:
        with zipfile.ZipFile(apk) as zf:
            names = set(zf.namelist())
    except (OSError, zipfile.BadZipFile) as exc:
        return [f"{apk}: unreadable APK: {exc}"]

    required = {"AndroidManifest.xml", "resources.arsc"}
    missing = sorted(required - names)
    if missing:
        errors.append(f"{apk}: missing {', '.join(missing)}")
    dex = sorted(name for name in names if name.startswith("classes") and name.endswith(".dex"))
    if dex:
        errors.append(f"{apk}: RRO must not contain DEX: {', '.join(dex)}")
    native = sorted(name for name in names if name.startswith("lib/") and name.endswith(".so"))
    if native:
        errors.append(f"{apk}: RRO must not contain native code")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("apks", nargs="+", type=Path)
    args = parser.parse_args()
    errors: list[str] = []
    for apk in args.apks:
        errors.extend(audit(apk))
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"resource-only APK audit passed ({len(args.apks)} APKs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
