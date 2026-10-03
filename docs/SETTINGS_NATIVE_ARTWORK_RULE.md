# Settings native-artwork rule

The old clean-room Settings overlay replaced `settings_satellite_network_ic` with a generic 32dp vector.

ColorOS 17 already provides its own current light/dark satellite icon resources, so the v0.2.0 branch removes that replacement from the shipping module.

Settings is now styled by:

- the ROM's original drawable geometry;
- the ColorOS 17 native UXDesign/Monet pipeline;
- the semantic accent RRO where the target exposes an explicit accent token;
- component-scoped hooks only when separately justified.

No generic Settings artwork is shipped in v0.2.0.
