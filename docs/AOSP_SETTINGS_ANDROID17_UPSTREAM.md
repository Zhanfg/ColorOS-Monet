# Android 17 AOSP Settings upstream verification

The ColorOS 17 Settings package contains Android 17 Expressive resources that closely track AOSP Settings/SettingsLib.

Authoritative upstream for this reference is **android.googlesource.com**, not the GitHub AOSP mirror. The Android 17 platform manifest sets its default revision to `android17-release`; the public GitHub mirror may not expose that branch.

The CI verifier:

`tools/verify_aosp_settings_upstream.py`

resolves the exact current Gitiles commit for:

`platform/packages/apps/Settings @ refs/heads/android17-release`

and verifies representative Expressive resources directly from that revision.

The generated lock artifact is:

`dist/aosp-settings-upstream.lock`

This means the project uses two distinct pinned/verified upstreams:

1. Google Material Symbols for the complete generic glyph catalog.
2. Android 17 AOSP Settings for component-level Expressive integration and wrapper resources.

Material Symbols is a glyph source; AOSP Settings is the reference for how those/related assets are wired into Settings components.


## Exact pinned revision

The first verified Android 17 Settings snapshot is pinned to:

`213829fb67f5e070029e0513a088f31bc8f5c1ed`

tree:

`f41bf360ab496bb4c018a33f93b74858b8ed223c`

The verifier now distinguishes:

- `branch_head`: the moving `android17-release` head;
- `pinned_commit`: the immutable revision used by this project;
- `update_available`: whether upstream has advanced.

A branch advance does not silently change our icon/component reference. Updating the pin must be an explicit reviewed commit.
