#!/usr/bin/env python3
"""Reject disruptive commands from module runtime scripts."""
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "module"
PATTERNS = {
    "device reboot": re.compile(r"\breboot\b"),
    "broad process termination": re.compile(r"\b(?:pkill|killall)\b"),
    "application force stop": re.compile(r"\bam\s+force-stop\b"),
    "application data clear": re.compile(r"\bpm\s+clear\b"),
    "init service stop": re.compile(r"\b(?:setprop\s+ctl\.stop|stop\s+(?:audioserver|surfaceflinger|zygote))\b"),
    "application data deletion": re.compile(r"\brm\s+-[^\n]*r[^\n]*f[^\n]*/data/(?:data|user|user_de)/"),
}


def runtime_files() -> list[Path]:
    files = list(MODULE.glob("*.sh"))
    bin_dir = MODULE / "bin"
    if bin_dir.is_dir():
        files.extend(path for path in bin_dir.rglob("*") if path.is_file())
    return sorted(files)


def executable_lines(path: Path) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lines.append((number, raw))
    return lines


def main() -> int:
    errors: list[str] = []
    for path in runtime_files():
        rel = path.relative_to(ROOT)
        try:
            lines = executable_lines(path)
        except UnicodeDecodeError:
            errors.append(f"{rel}: runtime helper must be UTF-8 text")
            continue
        for number, line in lines:
            for label, pattern in PATTERNS.items():
                if pattern.search(line):
                    errors.append(f"{rel}:{number}: prohibited {label}: {line.strip()}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"runtime safety audit passed ({len(runtime_files())} scripts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
