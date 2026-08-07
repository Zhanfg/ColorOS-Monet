# COE 2.5 integration notes

## Status change

The earlier revision of this document treated the project-owner-supplied `COE 2.5.apk` as reference-only material. That is no longer the requested architecture.

The current requirement is: **COE 2.5 itself is the user-facing frontend.**

The public repository still does not store or redistribute the APK. Instead, private/device-integration builds inject the user-supplied binary at packaging time. See [`FRONTEND_COE.md`](FRONTEND_COE.md).

## Supplied package metadata

| Field | Value |
|---|---|
| SHA-256 | `afe7d36bac69127d6962158d04792c48020bf6dd082fad6ca2a2495c5e43b0f7` |
| Package | `one.dot.couiexpressive` |
| Version marker | `2.5.0.260802(25)` |
| Settings activity | `one.dot.couiexpressive.ui.SettingsActivity` |
| Launcher alias | `one.dot.couiexpressive.LauncherActivityAlias` |
| Xposed entry | `one.dot.couiexpressive.hooks.HookEntry` |
| UI stack | Jetpack Compose / Material 3 |

Static inspection also shows substantial launcher, Settings and SystemUI behavior code, so this APK is not merely a skin. It contains its own Xposed behavior layer.

## Current architecture

```text
COE APK
  ├─ settings UI / user interaction
  └─ optional COE LSPosed behavior hooks

ColorOS Monet module
  ├─ Rust monetctl
  ├─ CMONET01 package verification and state
  ├─ fabricated-overlay resource backend
  └─ wallpaper/resource watcher
```

The root module never silently enables LSPosed scopes. COE behavior activation remains explicit and user-controlled.

## Why both layers remain

A fabricated resource overlay can replace compatible resources but cannot reliably implement runtime layout restructuring, gesture interception, view animation, state-machine changes, media integration or method-level behavior. COE already contains behavior hooks for those surfaces.

Conversely, the Rust/CMONET backend provides deterministic component packaging, digest verification, resource synchronization, backend logs and an APK-per-target-free resource model.

For the current integration milestone, these two layers coexist. A later bridge may translate selected COE preference state into native CMONET component state, but the project does not claim that every COE toggle is currently reimplemented by Rust.

## Distribution boundary

The user-supplied COE binary is an external frontend. It is injected only with `tools/package_module.py --frontend-apk ...` and remains ignored by Git. This avoids converting a public source repository into a redistribution channel for a binary whose upstream licensing terms are not established in this repository.
