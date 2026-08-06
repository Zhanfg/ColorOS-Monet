#!/usr/bin/env python3
"""Fail CI when proprietary payloads, signing secrets, or generated APKs enter source control."""
from __future__ import annotations
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_SUFFIXES = {".apk", ".apks", ".xapk", ".jks", ".keystore", ".p12", ".pk8", ".pem", ".der"}
FORBIDDEN_NAMES = {"key.properties", "signing.properties", "local.properties"}
SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|token|password|private[_-]?key)\s*[:=]\s*[^<\s][^\s]*"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]
ALLOW_SECRET_SCAN = {"tools/audit_repository.py", ".github/workflows/release.yml", "docs/RELEASE_SIGNING.md"}

errors = []
for path in ROOT.rglob("*"):
    if not path.is_file() or ".git" in path.parts or "build" in path.parts:
        continue
    rel = path.relative_to(ROOT).as_posix()
    if path.suffix.lower() in FORBIDDEN_SUFFIXES or path.name in FORBIDDEN_NAMES:
        errors.append(f"forbidden binary/secret file: {rel}")
        continue
    if rel not in ALLOW_SECRET_SCAN:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"unexpected non-text source file: {rel}")
            continue
        for line in text.splitlines():
            if "System.getenv(" in line or "secrets." in line:
                continue
            for pattern in SECRET_PATTERNS:
                if pattern.search(line):
                    errors.append(f"possible secret in: {rel}")
                    break
            else:
                continue
            break
if errors:
    print("\n".join(errors), file=sys.stderr)
    raise SystemExit(1)
print("clean-room repository audit passed")
