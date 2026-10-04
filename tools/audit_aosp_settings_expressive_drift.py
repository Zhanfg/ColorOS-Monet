#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

PREFIX = ")]}'\n"

def fetch_json(url: str):
    req = urllib.request.Request(
        url, headers={"User-Agent": "ColorOS-Monet-aosp-drift/1"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        text = resp.read().decode("utf-8")
    if text.startswith(PREFIX):
        text = text[len(PREFIX):]
    return json.loads(text)

def config(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        out[key.strip()] = value.strip()
    return out

def resolve(base: str, ref: str) -> str:
    data = fetch_json(f"{base}/+/{ref}?format=JSON")
    commit = data.get("commit") or data.get("id")
    if not commit:
        raise RuntimeError(f"cannot resolve {ref}")
    return commit

def drawable_names(base: str, ref: str) -> set[str]:
    data = fetch_json(f"{base}/+/{ref}/res/drawable?format=JSON")
    result = set()
    for entry in data.get("entries", []):
        name = entry.get("name", "")
        if name.endswith(".xml") and "expressive" in name.lower():
            result.add(name[:-4])
    return result

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()

    cfg = config(args.source)
    base = cfg["repository"].rstrip("/")
    branch_ref = cfg.get("branch_ref", f"refs/heads/{cfg['branch']}")
    pinned = cfg["pinned_commit"]

    branch_head = resolve(base, branch_ref)
    pinned_names = drawable_names(base, pinned)
    branch_names = drawable_names(base, branch_head)

    added = sorted(branch_names - pinned_names)
    removed = sorted(pinned_names - branch_names)
    common = sorted(pinned_names & branch_names)

    lines = [
        "# AOSP Settings Expressive drawable drift",
        "",
        f"pinned_commit={pinned}",
        f"branch_head={branch_head}",
        f"pinned_count={len(pinned_names)}",
        f"branch_count={len(branch_names)}",
        f"common_count={len(common)}",
        f"added_count={len(added)}",
        f"removed_count={len(removed)}",
        "",
        "## Added after pinned Android 17 r1 baseline",
        "",
    ]
    lines.extend(f"- {name}" for name in added)
    lines.extend(["", "## Removed from current android17-release branch", ""])
    lines.extend(f"- {name}" for name in removed)
    lines.extend(["", "## Policy", ""])
    lines.append(
        "Branch drift is review input only. Shipping mappings stay pinned until "
        "the current ColorOS target exposes/consumes the corresponding resource."
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        f"pinned={len(pinned_names)} branch={len(branch_names)} "
        f"added={len(added)} removed={len(removed)}"
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
