# Settings homepage icon architecture — ColorOS 17

This is now verified from the **actual current Settings.apk binary XML**, not
from resource-name heuristics.

## Result

The ColorOS 17 Settings homepage already uses a native Material/Expressive icon
architecture.

For the 25 category wrappers with an explicit foreground drawable:

- **24 / 25** directly embed a drawable whose resource name is Expressive.
- The remaining data-usage wrapper embeds the native `ic_settings_data_usage`.
- Search / AI-search wrappers use a different structure and are not part of this
  category-icon count.

Representative direct references:

```text
ic_homepage_about
  -> ic_settings_about_device_expressive

ic_homepage_battery
  -> ic_settings_battery_expressive

ic_homepage_display
  -> ic_settings_display_expressive

ic_homepage_network
  -> ic_settings_wireless_expressive

ic_homepage_notification
  -> ic_notifications_expressive

ic_homepage_sound
  -> ic_volume_up_expressive
```

## Exact wrapper geometry

Each verified category wrapper is a `layer-list`:

```text
24dp AdaptiveIconShapeDrawable
  ├─ categorical background color
  └─ 16dp foreground drawable
       inset/start/top = 4dp
```

The dimensions resolve to:

- `dashboard_tile_image_size = 24dp`
- `dashboard_tile_foreground_image_size = 16dp`
- `dashboard_tile_foreground_image_inset = 4dp`

This means replacing the whole homepage icon with a generic 24dp Material
Symbol would destroy a real native composition that already implements the
desired Expressive glyph treatment.

## Exact foreground construction

Most `*_expressive` foreground resources are themselves
`com.android.settings.widget.TintDrawable` wrappers over the corresponding
filled glyph.

Example:

```text
ic_settings_battery_expressive
  -> TintDrawable
  -> tint = homepage_battery_foreground
  -> drawable = ic_settings_battery_filled
```

The same pattern is present for about-device, accessibility, accounts, apps,
connected-device, help, notifications, display, emergency, location, privacy,
safety, security, system, wallpaper, wireless, storage, volume and others.

## Color model

The homepage category colors are **not one wallpaper-primary tint**.

They intentionally use categorical Material reference palettes:

- blue / blue-variant
- cyan
- green
- grey
- orange
- pink
- purple
- red
- yellow

Typical light/dark pairing is:

```text
background: palette tone 90 (light) / tone 80 (night)
foreground: palette tone 30
```

Examples from the current Settings resource table:

- blue: `#D0E4FF / #A1C9FF`, foreground `#04409F`
- green: `#BEEFBB / #80DA88`, foreground `#00522C`
- orange: `#FFDCC3 / #FFB683`, foreground `#753403`
- pink: `#FFD8EF / #FFAEE4`, foreground `#8D0053`
- red: `#FFDADC / #FFB3AE`, foreground `#8A1A16`

## Shipping decision

For Settings homepage category icons:

**KEEP THE COMPLETE NATIVE WRAPPER.**

Do not:

- replace it with a raw Material Symbol;
- flatten all categories to `system_primary`;
- remove the categorical background;
- enlarge the foreground to fill the 24dp slot;
- redraw the current Expressive foreground.

Material Symbols remains useful for glyph gaps elsewhere, but not as the first
source for homepage category icons because ColorOS already has the correct
Expressive assets and composition.

## Reproducibility

Derived metadata is stored in:

`compat/material-symbols/settings_homepage_native_expressive.tsv`

and can be regenerated from a user-supplied Settings.apk with:

```sh
python tools/extract_settings_homepage_native_expressive.py \
  --aapt2 /path/to/aapt2 \
  --settings-apk /path/to/Settings.apk \
  --output /tmp/settings_homepage_native_expressive.tsv
```

No vendor drawable/pathData is committed.
