# Settings homepage icon bridge build validation

The experiment builder has now been validated against the user's actual PJZ110
ColorOS 17 Settings APK rather than only against synthetic resource tables.

## Current homepage source split

The exact OPlus homepage has 42 icon-bearing rows:

- 24 -> `KEEP_NATIVE`
- 12 -> `NATIVE_EXPRESSIVE`
- 6 -> `MATERIAL_SYMBOL`

The six Material Symbol rows are currently:

- airplane mode -> `flight`
- Wi-Fi -> `wifi`
- Bluetooth settings -> `settings_bluetooth`
- screen lock -> `lock`
- account settings -> `manage_accounts`
- legal information -> `gavel`

All are from the pinned Google Material Symbols Rounded 24px upstream snapshot.

## Local build proof

Using the current ROM:

- `framework-res.apk`
- `Settings.apk`
- Android 17 `aapt2`

an experiment RRO was successfully linked with **18 drawable overrides**:

- 12 references redirect existing OPlus homepage resources to native
  `*_expressive` resources already present in the same Settings APK;
- 6 overrides embed the pinned Google Material Symbol vector geometry.

The linked overlay resource table resolves the twelve native aliases to the
expected current Settings resources, including:

- `ic_apps_expressive`
- `ic_help_expressive`
- `ic_notifications_expressive`
- `ic_settings_about_device_expressive`
- `ic_settings_battery_expressive`
- `ic_settings_display_expressive`
- `ic_settings_location_expressive`
- `ic_settings_privacy_expressive`
- `ic_settings_safety_center_expressive`
- `ic_settings_system_dashboard_expressive`
- `ic_settings_wallpaper_expressive`
- `ic_volume_up_expressive`

No vendor drawable bytes are copied into the public repository.

## Palette ownership fix

Official Material Symbols Android XML normally carries:

- `android:tint="?attr/colorControlNormal"`
- `android:fillColor="@android:color/white"`

The probe builder now strips the upstream tint owner and normalizes the white
fill to a literal white source mask while preserving Google's path geometry.

This is intentional because the real OPlus homepage preference classes already
own:

- two-tone category color;
- icon tint;
- warning/normal state;
- layout/container treatment.

Importing Material's own `colorControlNormal` would create a second palette
owner and break that contract.

## What this proves

It proves that the **resource bridge is buildable** and that all selected
resource names resolve on the current target.

It does not yet prove the final on-device visual result or OverlayManager
activation path.

Therefore the bridge remains under `experiments/` and is not included in the
shipping module.
