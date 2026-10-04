# Full ColorOS 17 icon inventory and Material Symbols candidate pass

This pass expands icon work from the Settings homepage to the complete current
ColorOS 17 target-dump set without changing any shipping artwork.

Source snapshot: the user's PJZ110 ColorOS 17 target dump used by the v0.2.0
compatibility work.

## Inventory result

After excluding obvious component surfaces, animation frames, masks, selectors,
library-prefixed resources and other non-glyph resources:

- **29 target packages**
- **12,279 icon-like drawable/mipmap resources**
- **6,282** generic-semantic candidates
- **593** OEM/product-specific candidates
- **439** state-machine assets
- **4,965** unresolved/review items

The package-level breakdown is stored in:

`compat/material-symbols/coloros17_full_icon_inventory_summary.tsv`

The inventory is reproducible with:

```sh
python tools/extract_coloros_icon_inventory.py \
  --aapt2 /path/to/aapt2 \
  --targets /path/to/ColorOS17_TargetDump/files/targets \
  --all-packages \
  --output /tmp/coloros17-icon-inventory.tsv
```

## Deterministic Material Symbols pass

The local inventory was joined against the pinned official Material Symbols
catalog:

`google/material-design-icons@737e3324305806514d7909874fa1818ae1808232`

Only deterministic matches were counted here; fuzzy-name suggestions were
excluded.

Result:

- **418 deterministic candidate rows across 26 packages**
- Settings: **100**
- SystemUI: **62**
- Launcher: **15**
- WirelessSettings: **12**
- NotificationManager: **7**

Match reasons:

- exact semantic core: **208**
- presentation suffix removed: **92**
- state suffix removed: **48**
- curated alias: **41**
- size suffix removed: **29**

These numbers are candidate discovery, **not replacement authorization**.

## Source precedence remains mandatory

Every candidate must pass this order:

1. current ColorOS native Expressive consumer/resource;
2. pinned AOSP Android 17 component Expressive implementation;
3. exact Google Material Symbol;
4. otherwise keep the OEM-native drawable.

An exact filename match does not override a proven native Expressive asset.

Examples:

- `ic_settings_display_expressive` already exists and has Android 17
  provenance: do not replace it with `display_settings` merely because the
  Google symbol is available.
- an OEM carrier/satellite/fingerprint/VOOC/device-art asset remains native even
  when a visually similar generic symbol exists.
- RSSI/battery/animation state assets are state machines and are never mapped
  one frame at a time.

## Next mapping stages

The 418 deterministic candidates are reviewed by actual consumer in this order:

1. Settings — first native Expressive gate, then only weak generic glyph gaps;
2. SystemUI — wait for exact QS/notification/media/volume/clock runtime binding;
3. Launcher — separate optional scope, not part of v0.2.0 system shipping;
4. remaining ColorOS apps — component-by-component, keeping product identity.

The project therefore now has a complete discovery path without turning
"Material Symbols exists" into "replace everything".
