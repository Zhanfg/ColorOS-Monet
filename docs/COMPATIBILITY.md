# Compatibility and validation

## Supported baseline

- Android 12 / SDK 31 or newer;
- ARM64;
- Magisk, KernelSU, or APatch module lifecycle;
- root access to `cmd overlay fabricate`.

## Policy boundary

Fabricated overlays do not bypass Android resource-overlay policy. A target may require an `overlayable` name, matching signature, actor authorization, or partition policy. A successful package build therefore does not prove device acceptance.

## Device validation sequence

```sh
su
/data/adb/modules/coloros_monet/bin/monetctl list
/data/adb/modules/coloros_monet/bin/monetctl apply-all
cmd overlay list --user 0
cat /data/adb/coloros-monet/service.log
cat /data/adb/coloros-monet/watcher.log
```

For a failed component, capture:

```sh
cmd overlay dump com.android.shell:<overlay_name>
logcat -b all -d | grep -Ei 'OverlayManager|idmap|fabricated|overlayable|coloros.monet'
```

Do not report a component as device-compatible until its target resources resolve and the application has been visually checked in both light and dark mode.
