# ColorOS 17 ART+ loader notes

Target audited: ColorOS 17 Launcher `com.android.launcher`, version 17.3.12.

These notes are from direct DEX inspection of the Launcher package extracted from the current ColorOS 17 DesktopSuite sample.

## Search priority

The Launcher path table in obfuscated class `Lzr/p;` places the writable ART+ tree before the built-in product tree:

1. `/data/oplus/uxicons/`
2. `/my_product/media/theme/uxicons/`

This is the main reason the generator can remain systemless: a generated package under the data tree can override a built-in package without modifying the Launcher APK or a read-only product partition.

Additional firmware fallback roots exist, including stock/region/carrier theme trees, but the functional app-icon lookup path uses the data/product priority above.

## Asset selection

The main loader in `Lzr/m;->w(...)` contains explicit asset names:

- `rec_night`
- `monochrome`
- `peb`
- `recfg`
- `daybg`
- `recbg`

The observed foreground decision order is:

1. dark-redraw condition -> `rec_night`
2. monochrome-theme condition -> `monochrome`
3. other special theme branches
4. peb-style condition -> `peb`
5. default -> `recfg`

Background resolves to `daybg` only in its dedicated style branch; normal ART+ uses `recbg`.

## Dark redraw condition

The helper corresponding to the `rec_night` branch logs `isDarkRedraw:` and resolves true when:

- icon theme == 2
- `IconConfig.isDarkModeIcon()` is true
- and either `IconConfig.isAlwaysNight()` or the runtime dark-mode condition is true

Therefore `rec_night` is a first-class ColorOS asset, not a generic runtime color filter.

## Monochrome branch

The monochrome helper is a separate icon-theme branch (observed theme value 3 plus the relevant theme-configuration predicate). This is independent from `rec_night`.

This is why the compiler generates both `rec_night.png` and `monochrome.png`.

## Large-icon variants

The Launcher constructs span suffixes for large icons, matching the ART+ convention:

- `_1x2`
- `_2x1`
- `_2x2`

The generator emits matching variants for `recbg`, `recfg`, `rec_night`, and `monochrome`.

## Cache-related surfaces found

The Launcher includes separate morph/icon cache paths and dark-icon state, including strings/classes corresponding to:

- `isDarkIconActive`
- `isDarkIconEnable`
- `clearMorphIconCache`
- `clearMorphIconCacheExceptSelf`
- `loadFromMorphIconCache`
- `updateMorphIconCache`
- `BaseIconCache`
- `IconCacheUpdateHandler`

The first generator build uses a conservative Launcher process reload after a completed batch rather than deleting Launcher databases. A later revision can replace this with a narrower native cache invalidation path after the relevant method contract is fully audited.

## Generator contract

The current compiler targets the confirmed ColorOS names and dimensions:

- 1x1: 240 x 240
- 1x2: 240 x 820
- 2x1: 820 x 240
- 2x2: 704 x 704

Adaptive icons are read as real foreground/background/monochrome layers. Legacy single-layer icons go through local, confidence-gated separation. Low-confidence cases preserve the original geometry rather than applying destructive segmentation.
