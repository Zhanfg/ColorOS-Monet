#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations
import argparse
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--monetctl", type=Path, required=True)
    parser.add_argument("--sources", type=Path, default=Path("build/component-src"))
    parser.add_argument("--output", type=Path, default=Path("build/components"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for old in args.output.glob("*.cmonet"):
        old.unlink()
    count = 0
    for source in sorted(args.sources.iterdir()):
        if not source.is_dir() or not (source / "component.json").is_file():
            continue
        output = args.output / f"{source.name}.cmonet"
        subprocess.run(
            [str(args.monetctl), "pack", str(source), str(output)], check=True
        )
        subprocess.run([str(args.monetctl), "verify", str(output)], check=True)
        count += 1
    if count == 0:
        raise RuntimeError("no component sources found")
    print(f"built {count} .cmonet components")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
