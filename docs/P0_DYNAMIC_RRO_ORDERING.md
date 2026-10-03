# Deterministic ColorOS 17 correction-layer ordering

The first P0 prototype used a static RRO with a large manifest priority. That is not a reliable ordering contract on modern Android when OverlayConfig is present.

v0.2.0 therefore builds the ColorOS 17 native-foundation correction layer as **mutable RROs**.

At boot, after PackageManager and OverlayManager are available, the service:

1. verifies the target package exists;
2. verifies the correction RRO is recognized;
3. enables the correction RRO;
4. requests `set-priority ... highest`;
5. verifies the RRO is actually enabled;
6. records `overlay dump` evidence.

This ordering is applied after the ordinary module overlays, so the native-foundation layer is the last mutable correction layer for its target.

The post-boot audit must still verify effective resource lookup. CI success alone is not treated as proof of runtime precedence.
