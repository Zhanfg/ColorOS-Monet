#!/usr/bin/env python3
"""Audit a user-supplied ColorOS 17 SystemUI.apk for native component XML evidence.

No vendor XML is emitted. The tool prints only selected element names, resolved
resource IDs/names and scalar values needed by the public architecture docs.
"""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

FILES = (
    "res/layout/oplus_volume_dialog.xml",
    "res/layout/vertical_volume_row.xml",
    "res/drawable/volume_dialog_background.xml",
    "res/drawable/notification_material_bg.xml",
    "res/drawable/notification_bg.xml",
    "res/color/notification_state_color_default.xml",
    "res/color/notification_focus_overlay_color.xml",
    "res/layout/oplus_qs_tile_1x1.xml",
    "res/layout/oplus_qs_tile_2x1.xml",
    "res/layout/oplus_qs_tile_2x2.xml",
    "res/layout/oplus_qs_tile_three_stage.xml",
    "res/drawable/status_bar_qs_tile_bg_active.xml",
    "res/drawable/status_bar_qs_tile_bg_inactive.xml",
)

KEEP = re.compile(
    r"(E: |OplusVolume|couiVerticalSeekBar|state_pressed|state_focused|"
    r"duplicateParentState|android:radius|android:color|android:alpha|"
    r"layout_width|layout_height|elevation|deformation)",
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

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--aapt2", type=Path, required=True)
    p.add_argument("--systemui", type=Path, required=True)
    args = p.parse_args()

    for name in FILES:
        print(f"### {name}")
        try:
            tree = run(args.aapt2, "dump", "xmltree", args.systemui, "--file", name)
        except subprocess.CalledProcessError:
            print("MISSING")
            continue
        for line in tree.splitlines():
            if KEEP.search(line):
                print(line)
        print()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
