#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

PREFIX = ")]}'\n"

def read_lock(path: Path) -> dict[str, str]:
    out = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        out[key.strip()] = value.strip()
    return out

def get(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "ColorOS-Monet-SetupDesign-Verifier/1"},
    )
    last = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code not in {429, 500, 502, 503, 504} or attempt == 3:
                raise
        except urllib.error.URLError as exc:
            last = exc
            if attempt == 3:
                raise
        time.sleep(2 ** attempt)
    raise RuntimeError(f"unreachable retry state: {last}")

def get_json(url: str) -> dict:
    text = get(url).decode("utf-8")
    if text.startswith(PREFIX):
        text = text[len(PREFIX):]
    return json.loads(text)

def get_text(repo: str, commit: str, path: str) -> str:
    url = f"{repo}/+/{commit}/{path}?format=TEXT"
    payload = get(url)
    return base64.b64decode(payload).decode("utf-8")

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()

    lock = read_lock(args.source)
    repo = lock["repository"].rstrip("/")
    tag = lock["release_tag"]
    pinned_commit = lock["release_commit"]

    tag_meta = get_json(f"{repo}/+/refs/tags/{tag}?format=JSON")
    resolved = tag_meta.get("commit") or tag_meta.get("id") or ""
    # Gitiles tag pages may expose tag object metadata rather than the peeled
    # commit. The file fetch below against the pinned commit is authoritative.
    if resolved and resolved not in {pinned_commit, lock.get("release_tag_object", "")}:
        print(f"note: tag metadata id={resolved}")

    selector_path = "main/res/drawable/sud_ic_switch_selector_expressive.xml"
    check_path = "main/res/drawable/sud_ic_switch_check_mark_expressive.xml"
    switch_path = "main/src/com/google/android/setupdesign/items/SwitchItem.java"

    selector = get_text(repo, pinned_commit, selector_path)
    check = get_text(repo, pinned_commit, check_path)
    switch = get_text(repo, pinned_commit, switch_path)

    failures = []
    if "sud_ic_switch_check_mark_expressive" not in selector:
        failures.append("selector does not reference checked Expressive glyph")
    if "colorPrimary" not in check:
        failures.append("checked glyph is not themed with colorPrimary")
    if "sud_ic_switch_selector_expressive" not in switch:
        failures.append("SwitchItem does not install Expressive selector")
    if not re.search(r"setThumbIconDrawable\s*\(\s*null\s*\)", switch):
        failures.append("SwitchItem unchecked path is not null thumb icon")
    if "shouldApplyGlifExpressiveStyle" not in switch:
        failures.append("SwitchItem missing Glif Expressive activation gate")

    if failures:
        print("SetupDesign verification failed:")
        for failure in failures:
            print(" -", failure)
        return 1

    output = "\n".join([
        f"repository={repo}",
        f"release_tag={tag}",
        f"pinned_commit={pinned_commit}",
        f"selector_path={selector_path}",
        f"check_path={check_path}",
        f"switch_item_path={switch_path}",
        "selector_refs_checked_glyph=1",
        "checked_glyph_uses_colorPrimary=1",
        "switch_item_expressive_gate=1",
        "unchecked_thumb_icon_null=1",
        "status=verified",
        "",
    ])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8")
    print(f"VERIFIED SetupDesign Android 17 @ {pinned_commit}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
