# COE APK frontend integration

## Decision

The project owner supplied **COE 2.5** and requires that APK to be the user-facing frontend, rather than using it only as a visual reference.

The resulting architecture is:

```text
COE APK (one.dot.couiexpressive)
    -> user settings / interaction surface
    -> optional LSPosed behavior layer owned by COE itself

ColorOS Monet root module
    -> Rust monetctl runtime
    -> CMONET01 component store
    -> fabricated-overlay resource backend
    -> wallpaper/resource re-application watcher
```

The COE APK is therefore treated as an external frontend binary. It is not reconstructed into a WebUI and is not copied into the public Git repository.

## Supplied package identity

Static inspection of the user-supplied APK found:

- package: `one.dot.couiexpressive`
- settings activity: `one.dot.couiexpressive.ui.SettingsActivity`
- launcher alias: `one.dot.couiexpressive.LauncherActivityAlias`
- Xposed entry point: `one.dot.couiexpressive.hooks.HookEntry`
- module marker: `moduleVersion=2.5.0.260802(25)`
- supplied APK SHA-256: `afe7d36bac69127d6962158d04792c48020bf6dd082fad6ca2a2495c5e43b0f7`

The APK contains its own Xposed behavior implementation. This project does **not** silently enable LSPosed scopes. The user remains in control of whether COE's behavior hooks are active.

## Packaging

Public/CI builds remain backend-only:

```bash
python tools/package_module.py \
  --runtime <monetctl> \
  --components build/components \
  --version <version> \
  --version-code <code> \
  --output <module.zip>
```

A private/device-integration build can inject the supplied frontend without committing it:

```bash
python tools/package_module.py \
  --runtime <monetctl> \
  --components build/components \
  --frontend-apk '/path/to/COE 2.5.apk' \
  --version <version> \
  --version-code <code> \
  --output <module.zip>
```

The packager stores it at `frontend/COE-2.5.apk` and writes a matching SHA-256 sidecar. Installer validation allows this one explicit APK path and continues to reject any other APK payload.

## Device behavior

After Android reports boot complete, `service.sh`:

1. detects whether `one.dot.couiexpressive` already exists;
2. attempts `pm install -r --user 0` for the bundled frontend;
3. preserves an already-installed package if Android rejects the bundled update;
4. records the result in `/data/adb/coloros-monet/frontend.status`;
5. continues with CMONET01 synchronization and fabricated-overlay application even if frontend installation fails.

The module Action now opens COE rather than toggling all components. It attempts the launcher alias first, then the settings activity, then a standard launcher intent.

## Uninstall boundary

Removing the ColorOS Monet module does not uninstall `one.dot.couiexpressive`. The package may predate the module or may have been updated independently, so automatic removal would be destructive.

## Current limitation

COE remains a closed external frontend/behavior package. The Rust backend does not yet consume every COE preference key as a native CMONET configuration protocol. Resource overlays and COE behavior hooks therefore coexist as two coordinated layers rather than pretending to be one fully unified implementation.
