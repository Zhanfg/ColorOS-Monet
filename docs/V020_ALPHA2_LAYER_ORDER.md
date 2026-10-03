# v0.2.0 alpha2 layer order

The ColorOS 17 build now has three distinct responsibilities:

1. **Native foundation** — restores ColorOS 17 geometry, divider, surface and state tokens that the legacy design overrode globally.
2. **MD3E semantic accent** — applies only the high-confidence primary accent color family to current ColorOS 17 resources.
3. **Optional native EXPRESSIVE palette** — disabled by default; users may opt into the ROM's own EXPRESSIVE Monet variant.

Both correction and semantic RROs are mutable and ordered at runtime. The semantic layer is enabled after the native foundation and contains no geometry or neutral-surface overrides.

This keeps MD3E visible without making it the owner of every visual token in ColorOS.
