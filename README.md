# ColorOS Monet

Clean-room Android Runtime Resource Overlay (RRO) project for ColorOS and selected applications.

## Included overlays

| Component | Target package | Scope |
|---|---|---|
| ColorOS Settings | `com.android.settings` | Original Monet satellite-network entry icon |
| X | `com.twitter.android` | Reviewed semantic color mapping |
| TIM | `com.tencent.tim` | QUI/TIM semantic color mapping |
| Coolapk | `com.coolapk.market` | Material and Coolapk semantic color mapping |

The repository contains **no original target APKs, copied module payloads, vendor artwork, signing keys, or decompiled application code**.

## Clean-room boundary

This repository was restarted from an empty base. The module installer, runtime scripts, build pipeline, resource generator, mappings, and satellite vector were authored specifically for this project. Earlier third-party module APKs are not included and are not used as build inputs.

Resource names in `mapping/colors.tsv` are compatibility identifiers. Their semantic roles were manually reviewed against APKs supplied by the device owner. The mappings do not include application bytecode or proprietary assets.

## Build

Requirements:

- JDK 17
- Android SDK platform 35 and build-tools 35.0.0
- Python 3.10+

```bash
python tools/build_overlays.py \
  --variant debug \
  --version-name dev \
  --version-code 1
python tools/package_module.py \
  --variant debug \
  --version dev \
  --version-code 1 \
  --output dist/ColorOS-Monet-dev.zip
```

The command-line builder uses `aapt2`, `zipalign`, and `apksigner` directly so every overlay APK is resource-only and contains no DEX. Debug builds use a locally generated Android debug signing identity. Public releases require a stable signing key supplied through encrypted CI secrets; no key is stored in this repository.

## Installation

Install the generated module ZIP with Magisk, KernelSU, or APatch, then reboot. The module action menu can enable or disable each overlay.

RRO activation is firmware-dependent. Check `/data/adb/coloros-monet/overlay-status.log` when a target application does not change appearance.

## Supported versions

Mappings are version-sensitive. The initial compatibility data was reviewed against:

- X 12.13.0
- TIM 4.1.0.4050
- Coolapk package `com.coolapk.market` from the supplied base APK
- ColorOS 16 Settings resource `settings_satellite_network_ic`

## License

Project-authored source is licensed under Apache-2.0. Product names and package names are used only for compatibility identification. Third-party applications and trademarks remain the property of their respective owners.
