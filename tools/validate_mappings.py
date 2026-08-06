#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
for overlay in sorted((root / "overlays").iterdir()):
    mapping_dir = overlay / "mapping"
    if not mapping_dir.is_dir():
        continue
    mapping = (mapping_dir / "colors.tsv") if (mapping_dir / "colors.tsv").is_file() else mapping_dir
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(
            [sys.executable, str(root / "tools/generate_colors.py"), "--mapping", str(mapping), "--output", td],
            check=True,
        )
        assert (Path(td) / "values/colors.xml").is_file()
        assert (Path(td) / "values-night/colors.xml").is_file()
print("mapping validation passed")
