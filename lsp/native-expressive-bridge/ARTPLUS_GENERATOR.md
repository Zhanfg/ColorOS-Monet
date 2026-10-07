# ColorOS 17 ART+ Generator

`0.2.1-alpha1` adds an on-device ART+ compiler to the existing native expressive bridge.

Pipeline:

1. Enumerate launcher apps.
2. For `AdaptiveIconDrawable`, keep the app's native foreground/background layers and native monochrome when present.
3. For legacy bitmap icons, estimate the border/corner background, run conservative soft separation, and fall back to the intact source whenever confidence is low.
4. Generate `recfg`, `recbg`, `rec_night`, `monochrome` and ColorOS large-icon span variants.
5. Write through root to `/data/oplus/uxicons/{package}`, which ColorOS 17 Launcher checks before the built-in `/my_product/media/theme/uxicons/` tree.

This is deliberately offline: no image API and no large segmentation model are required.
