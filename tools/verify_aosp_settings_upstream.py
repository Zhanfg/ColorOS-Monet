#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

PREFIX = ")]}'\n"

def request(url: str, *, accept: str | None = None) -> urllib.request.Request:
    headers = {"User-Agent": "ColorOS-Monet-upstream-verifier/2"}
    if accept:
        headers["Accept"] = accept
    token = os.environ.get("GITHUB_TOKEN", "")
    if token and "api.github.com" in url:
        headers["Authorization"] = f"Bearer {token}"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
    return urllib.request.Request(url, headers=headers)

def fetch_bytes(url: str, *, accept: str | None = None, attempts: int = 6) -> bytes:
    req = request(url, accept=accept)
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=40) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code not in {429, 500, 502, 503, 504} or attempt == attempts - 1:
                raise
        except urllib.error.URLError as exc:
            last = exc
            if attempt == attempts - 1:
                raise
        time.sleep(min(30, 2 ** attempt))
    raise RuntimeError(f"unreachable retry state: {last}")

def fetch_text(url: str, *, attempts: int = 6) -> str:
    return fetch_bytes(url, attempts=attempts).decode("utf-8")

def fetch_json(url: str, *, attempts: int = 6):
    text = fetch_text(url, attempts=attempts)
    if text.startswith(PREFIX):
        text = text[len(PREFIX):]
    return json.loads(text)

def fetch_gitiles_file(base: str, ref: str, path: str) -> bytes:
    url = f"{base}/+/{ref}/{path}?format=TEXT"
    raw = fetch_text(url).strip()
    return base64.b64decode(raw)

def resolve_gitiles_ref(base: str, ref: str) -> tuple[str, dict]:
    data = fetch_json(f"{base}/+/{ref}?format=JSON")
    commit = data.get("commit") or data.get("id")
    if not commit:
        raise RuntimeError(f"Gitiles response did not expose commit id for {ref}: {data.keys()}")
    return commit, data

def github_commit(mirror: str, sha: str) -> dict:
    return fetch_json(f"{mirror.rstrip('/')}/commits/{sha}")

def github_file(mirror: str, sha: str, path: str) -> bytes:
    # GitHub contents API can return base64 JSON and is a useful independent
    # fallback when android.googlesource.com is temporarily 5xx.
    quoted = urllib.parse.quote(path, safe="/")
    data = fetch_json(f"{mirror.rstrip('/')}/contents/{quoted}?ref={sha}")
    if data.get("encoding") != "base64":
        raise RuntimeError(f"unexpected GitHub contents encoding for {path}: {data.get('encoding')}")
    return base64.b64decode(data["content"])

# urllib.parse is intentionally imported late to keep the request helpers grouped.
import urllib.parse

def read_cfg(path: Path) -> dict[str, str]:
    cfg: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        cfg[key.strip()] = value.strip()
    return cfg

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()

    cfg = read_cfg(args.source)
    base = cfg.get(
        "repository",
        "https://android.googlesource.com/platform/packages/apps/Settings",
    ).rstrip("/")
    mirror = cfg.get(
        "github_mirror",
        "https://api.github.com/repos/aosp-mirror/platform_packages_apps_settings",
    ).rstrip("/")
    branch = cfg.get("branch", "android17-release")
    branch_ref = cfg.get("branch_ref", f"refs/heads/{branch}")
    pinned = cfg["pinned_commit"]

    branch_head = ""
    branch_status = "verified"
    try:
        branch_head, _ = resolve_gitiles_ref(base, branch_ref)
    except Exception as exc:
        # The branch-head check is drift monitoring, not the immutable-source
        # trust anchor. Do not make a pinned build flaky because Gitiles is 5xx.
        branch_status = f"unavailable:{type(exc).__name__}"

    pinned_source = ""
    pinned_tree = ""
    try:
        pinned_commit, pinned_meta = resolve_gitiles_ref(base, pinned)
        if pinned_commit != pinned:
            raise RuntimeError(f"pinned commit did not resolve exactly: {pinned} -> {pinned_commit}")
        pinned_tree = pinned_meta.get("tree", "")
        pinned_source = "gitiles"
    except Exception:
        meta = github_commit(mirror, pinned)
        if meta.get("sha") != pinned:
            raise RuntimeError(f"GitHub mirror did not resolve pinned commit exactly: {meta.get('sha')}")
        pinned_tree = meta.get("commit", {}).get("tree", {}).get("sha", "")
        pinned_source = "github_mirror"

    required = [
        "res/drawable/ic_settings_display_expressive.xml",
        "res/drawable/ic_settings_privacy_expressive.xml",
        "res/drawable/ic_settings_security_expressive.xml",
        "res/drawable/ic_settings_location_expressive.xml",
        "res/drawable/ic_notifications_expressive.xml",
        "res/drawable/ic_help_expressive.xml",
    ]

    verified = []
    for path in required:
        data = b""
        file_source = ""
        try:
            data = fetch_gitiles_file(base, pinned, path)
            file_source = "gitiles"
        except Exception:
            data = github_file(mirror, pinned, path)
            file_source = "github_mirror"
        if not data.strip():
            raise RuntimeError(f"empty upstream file: {path}")
        verified.append((path, len(data), file_source))

    if branch_head:
        update_available = "1" if branch_head != pinned else "0"
    else:
        update_available = "unknown"

    out = [
        f"repository={base}",
        f"github_mirror={mirror}",
        f"branch={branch}",
        f"branch_ref={branch_ref}",
        f"branch_head={branch_head or 'unavailable'}",
        f"branch_status={branch_status}",
        f"pinned_commit={pinned}",
        f"pinned_tree={pinned_tree}",
        f"pinned_verification_source={pinned_source}",
        f"update_available={update_available}",
        "status=verified_pinned",
        f"verified_file_count={len(verified)}",
    ]
    for i, (path, size, file_source) in enumerate(verified, 1):
        out.append(f"verified_file_{i}={path}|{size}|{file_source}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
