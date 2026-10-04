#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
import subprocess
import tempfile
import zipfile
from collections import Counter
from pathlib import Path

PACKAGE_RE = re.compile(r"package: name='([^']+)'")
RESOURCE_RE = re.compile(r"^\s*resource\s+0x[0-9a-fA-F]+\s+([^/\s]+)/(.+?)\s*$")

DEFAULT_PACKAGES = {
    "com.android.settings",
    "com.android.systemui",
    "com.android.launcher",
    "com.oplus.wirelesssettings",
    "com.oplus.notificationmanager",
    "com.oplus.systemui.plugins",
}

LIBRARY_PREFIXES = (
    "abc_", "mtrl_", "material_", "coui_", "btn_", "design_", "test_",
    "notification_template_", "common_",
)

ICON_PATTERN = re.compile(
    r"(^ic_|_ic$|_ic_|^icon_|_icon$|_icon_|^qs_|^stat_sys_|"
    r"^status_bar_|^notification_|^volume_|^media_|^settings_|^affordance_)",
    re.I,
)
NON_ICON_PATTERN = re.compile(
    r"(background|_bg$|_bg_|divider|mask|shadow|ripple|selector|shape|"
    r"gradient|scrim|panel|layout|anim|animation|frame|progress|track|"
    r"thumb|wallpaper|screenshot|placeholder|decor|preview|overlay)",
    re.I,
)

def run(*args: object) -> str:
    return subprocess.run(
        [str(x) for x in args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    ).stdout

def classify(name: str) -> str:
    n = name.lower()
    if re.search(
        r"(wifi_[4567]?_?(lock_)?signal_[0-4]|mobiledata|stat_sys_|"
        r"signal_[0-4]|strength_[0-4]|level_[0-4])",
        n,
    ):
        return "STATE_ASSET"
    if re.search(
        r"(oplus|coloros|oneplus|breathing_light|dirac|dolby|tidal|aod_|"
        r"fingerprint|fp_|clone_app|private_profile|work_app|fold_|foldable|"
        r"personality|fluid_seeding|desktop_mode|flexible_|children_mode|"
        r"device_ota|device_market|reverse_charge|supervooc|vooc)",
        n,
    ):
        return "OEM_SPECIFIC"
    if re.search(
        r"(search|settings|back|close|clear|add|delete|remove|edit|share|"
        r"info|help|home|camera|flashlight|bluetooth|wifi|vpn|nfc|airplane|"
        r"battery|language|display|dark|light|security|lock|notifications?|"
        r"volume|mic|keyboard|phone|call|message|calendar|clock|alarm|download|"
        r"upload|refresh|more|menu|expand|collapse|arrow|qr|scanner|print|"
        r"location|accessibility|account|person|storage|memory|apps?|privacy)",
        n,
    ):
        return "GENERIC_CANDIDATE"
    return "REVIEW"

def compact_apk(source: Path, output: Path) -> None:
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as z:
        z.write(source / "AndroidManifest.xml", "AndroidManifest.xml")
        z.write(source / "resources.arsc", "resources.arsc")

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--aapt2", type=Path, required=True)
    p.add_argument("--targets", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--package", action="append", dest="packages")
    args = p.parse_args()

    packages = set(args.packages or DEFAULT_PACKAGES)
    rows = []

    with tempfile.TemporaryDirectory(prefix="cos17-icon-inventory-") as td:
        temp = Path(td)
        for source in sorted(x for x in args.targets.iterdir() if x.is_dir()):
            manifest = source / "AndroidManifest.xml"
            arsc = source / "resources.arsc"
            if not manifest.is_file() or not arsc.is_file():
                continue

            apk = temp / f"{source.name}.apk"
            compact_apk(source, apk)
            badging = run(args.aapt2, "dump", "badging", apk)
            match = PACKAGE_RE.search(badging)
            package = match.group(1) if match else ""
            if package not in packages:
                continue

            resources = run(args.aapt2, "dump", "resources", "--no-values", apk)
            for line in resources.splitlines():
                match = RESOURCE_RE.match(line)
                if not match:
                    continue
                resource_type, name = match.groups()
                name = name.removesuffix(" PUBLIC")
                lower = name.lower()
                if resource_type not in {"drawable", "mipmap"}:
                    continue
                if lower.startswith("$") or lower.startswith(LIBRARY_PREFIXES):
                    continue
                if not ICON_PATTERN.search(lower) or NON_ICON_PATTERN.search(lower):
                    continue
                rows.append({
                    "target_package": package,
                    "resource_type": resource_type,
                    "resource_name": name,
                    "classification": classify(name),
                    "source_target": source.name,
                })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "target_package", "resource_type", "resource_name",
        "classification", "source_target",
    ]
    with args.output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    print(f"rows={len(rows)}")
    print(f"packages={len({r['target_package'] for r in rows})}")
    for key, count in Counter(r["classification"] for r in rows).most_common():
        print(f"{key}={count}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
