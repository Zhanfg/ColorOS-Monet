# Architecture

## 1. Module base

The module uses `SKIPMOUNT=true`. It does not place files under `system/`,
`product/`, `vendor/`, or `system_ext/`, and it does not rely on bind mounts.

The remaining shell files are lifecycle adapters required by Magisk, KernelSU,
and APatch:

- `customize.sh`: architecture, SDK, package-header, and payload checks;
- `post-fs-data.sh`: synchronizes packaged components into persistent storage;
- `service.sh`: waits for boot, applies defaults, and launches the watcher;
- `action.sh`: toggles global enablement;
- `uninstall.sh`: disables project-owned objects and removes state.

All component decisions and package parsing are implemented in Rust.

## 2. Runtime and component container

`monetctl` provides:

- deterministic `.cmonet` packing;
- fixed-header and SHA-256 verification;
- path-traversal and archive-entry validation;
- atomic component installation;
- default-state initialization based on installed target packages;
- exclusive component groups;
- runtime overlay registration and enable/disable control;
- dynamic palette fingerprint monitoring.

The runtime never performs broad `killall`, `pkill`, bind mount, or recursive
system scan operations.

The fixed `CMONET01` header allows the future WebUI to reject unrelated files
before decompressing them and to display verified manifest metadata without
installing an APK.

## 3. Resource backend

The implemented resource backend is `fabricated-overlay`.

- Colors and strings are grouped into one fabricated overlay per component.
- Independently authored drawable Binary XML files are grouped where supported.
- Boolean, integer, dimension, animation, mipmap, and complex resources use
  deterministic project-owned overlay identifiers.
- All generated identifiers are saved so rollback disables only objects created
  by this project.

Before calling `cmd overlay fabricate`, file resources are copied into a
short-lived directory under `/data/local/tmp` with readable permissions.
OverlayManager consumes them during registration; the scratch directory is then
removed.

## 4. Behavior backend boundary

The owner-supplied COE 2.5 reference demonstrates runtime behavior that a
resource overlay cannot reproduce: layout restructuring, gesture interception,
stateful animation, media integration, and process-specific compatibility
logic. See [`COE_2_5_REFERENCE.md`](COE_2_5_REFERENCE.md).

ColorOS Monet therefore separates:

1. **resource components**, handled by the implemented fabricated-overlay path;
2. **behavior operators**, which will be provided by one project-owned,
   version-gated runtime bridge rather than one APK per target;
3. **component packages**, which remain non-executable `.cmonet` data files.

The behavior bridge is not complete in the current branch. No document or
release may describe resource-only coverage as equivalent to a runtime-hook
module. The reserved backend must fail closed until the loader, crash guard,
rollback, and device tests exist.

## 5. Build-time asset compiler

Source components store independent, auditable text XML. CI preprocesses local
references and compiles the XML with `aapt2` into Android Binary XML. The link
APK is temporary and discarded. Only extracted Binary XML is added to
`.cmonet` packages.

If an XML depends on a proprietary local drawable graph that cannot be resolved
without copying third-party geometry, the compiler substitutes an independent
project fallback. This preserves package validity without copying protected path
data.

## 6. Backends

| Backend | State | Purpose |
|---|---|---|
| `fabricated-overlay` | Implemented | APK-free Android OverlayManager path |
| `systemless-rro` | Reserved | Compatibility fallback; not emitted by runtime v2 |
| `zygisk-resource` | Reserved, fail-closed | Future behavior/resource bridge for policy-protected targets |

Detailed capability routing is recorded in [`BACKEND_MATRIX.md`](BACKEND_MATRIX.md).
