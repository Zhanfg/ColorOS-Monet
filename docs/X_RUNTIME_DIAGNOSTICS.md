# X runtime diagnostics

## Two independent failure planes

The X target can fail in two different layers that must not be conflated:

1. **RRO acceptance** — Android may reject or ignore `XMonet.apk` because of target `overlayable` policy, signature restrictions, idmap generation, a missing resource, package placement, or firmware-specific OverlayManager behavior.
2. **Target application stability** — the supplied X package includes Piko modifications. A crash can instead come from patch/version incompatibility, application anti-tamper logic, signing or split-package mismatch, resource-table rebuilding, or another modification unrelated to the RRO.

A successful `aapt2` build proves only that the overlay APK is structurally valid. It does not prove that the device accepted the overlay or that the modified target APK is stable.

## Runtime guard

At boot, `module/service.sh` now verifies all of the following before recording an overlay as accepted:

- the target package is visible to PackageManager;
- the overlay package is visible to PackageManager;
- `cmd overlay enable` returns successfully;
- OverlayManager reports the overlay as enabled.

When acceptance fails, the module disables that overlay again and records a machine-readable guard result in:

```text
/data/adb/coloros-monet/overlay-status.log
```

The guard does not restart the target application, SystemUI, SurfaceFlinger, Zygote, or any other service.

## X doctor

The module action menu exposes a read-only X diagnostic path. It collects:

- device, firmware, SDK, and SELinux state;
- target and overlay package paths, versions, splits, ABI, and hashes;
- OverlayManager list/dump output;
- representative resource lookups;
- matching idmap cache entries and `idmap2 dump` output when available;
- application exit history;
- filtered crash, resource, OverlayManager, idmap, Piko, and X log entries.

Reports are written to:

```text
/sdcard/Download/ColorOS_Monet_X_Doctor_<timestamp>.tar.gz
/sdcard/Download/ColorOS_Monet_X_Doctor_<timestamp>.tar.gz.sha256
```

The unpacked copy remains under `/data/adb/coloros-monet/reports/` for local inspection.

## Safety boundary

The doctor is observational. It does not:

- alter target or overlay APKs;
- delete application data;
- change permissions or signing state;
- restart applications or system services;
- modify framework, vendor, product, or ODM files.

The resulting report is required before assigning an exact cause to the X crash or failed Monet activation.
