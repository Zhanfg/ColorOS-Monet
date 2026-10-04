#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "compat/material-symbols/upstream_manifest.lock"
MATERIAL = ROOT / "compat/material-symbols/upstream.lock"
ANDROID17 = ROOT / "compat/material-symbols/android17-expressive-upstream.lock"
SETTINGS = ROOT / "compat/material-symbols/aosp-settings.source"
SETUP = ROOT / "compat/material-symbols/setupdesign.source"

def read(path: Path) -> dict[str, str]:
    out = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        k, v = raw.split("=", 1)
        out[k.strip()] = v.strip()
    return out

def main() -> int:
    m = read(MANIFEST)
    material = read(MATERIAL)
    android17 = read(ANDROID17)
    settings = read(SETTINGS)
    setup = read(SETUP)

    checks = [
        ("google_material_symbols_commit", material.get("ref")),
        ("aosp_settings_commit", settings.get("pinned_commit")),
        ("aosp_settings_commit", android17.get("settings_release_commit")),
        ("aosp_frameworks_base_commit", android17.get("frameworks_base_release_commit")),
        ("aosp_setupdesign_commit", setup.get("release_commit")),
    ]

    failures = []
    for key, actual in checks:
        expected = m.get(key)
        if not expected:
            failures.append(f"manifest missing {key}")
        elif actual != expected:
            failures.append(f"{key}: manifest={expected} source={actual}")

    expected_order = (
        "COLOROS_NATIVE_EXPRESSIVE>AOSP_SETTINGS_OR_SETTINGSLIB>"
        "AOSP_SETUPDESIGN>GOOGLE_MATERIAL_SYMBOLS>KEEP_NATIVE"
    )
    if m.get("fallback_order") != expected_order:
        failures.append("fallback_order drifted")

    if failures:
        print("upstream manifest violations:")
        for failure in failures:
            print(" -", failure)
        return 1

    print("upstream manifest ok")
    for key, _ in checks:
        print(f"{key}={m[key]}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
