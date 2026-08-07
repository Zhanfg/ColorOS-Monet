#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import zipfile
from pathlib import Path

MAGIC = b"CMONET01"


def audit_component(data: bytes, name: str) -> str:
    if len(data) < 128 or data[:8] != MAGIC:
        raise ValueError(f"{name}: invalid CMONET01 header")
    version, header_size = struct.unpack_from("<HH", data, 8)
    manifest_len, payload_len = struct.unpack_from("<QQ", data, 16)
    if version != 1 or header_size != 128:
        raise ValueError(f"{name}: unsupported component format")
    if len(data) != 128 + manifest_len + payload_len:
        raise ValueError(f"{name}: length mismatch")
    manifest = data[128 : 128 + manifest_len]
    payload = data[128 + manifest_len :]
    if hashlib.sha256(manifest).digest() != data[32:64]:
        raise ValueError(f"{name}: manifest digest mismatch")
    if hashlib.sha256(payload).digest() != data[64:96]:
        raise ValueError(f"{name}: payload digest mismatch")
    return json.loads(manifest)["id"]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("module", type=Path)
    args = p.parse_args()
    with zipfile.ZipFile(args.module) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError(f"bad zip entry {bad}")
        names = archive.namelist()
        required = {
            "module.prop", "customize.sh", "service.sh", "post-fs-data.sh",
            "action.sh", "uninstall.sh", "bin/monetctl",
            "META-INF/com/google/android/update-binary",
            "META-INF/com/google/android/updater-script",
        }
        missing = required - set(names)
        if missing:
            raise ValueError(f"missing {sorted(missing)}")
        apks = [name for name in names if name.lower().endswith(".apk")]
        if apks:
            raise ValueError(f"APK payload forbidden: {apks}")
        mounted = [name for name in names if name.startswith(("system/", "product/", "vendor/", "system_ext/"))]
        if mounted:
            raise ValueError(f"system mount payload forbidden: {mounted[:5]}")
        runtime = archive.read("bin/monetctl")
        if not runtime.startswith(b"\x7fELF"):
            raise ValueError("monetctl is not an ELF executable")
        components = [name for name in names if name.startswith("components/") and name.endswith(".cmonet")]
        if len(components) != 40:
            raise ValueError(f"expected exactly 40 components, got {len(components)}")
        ids = {audit_component(archive.read(name), name) for name in components}
        if len(ids) != 40:
            raise ValueError("duplicate component IDs")
    print(f"PASS module={args.module} components=40 apk_payloads=0 mount_payloads=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
