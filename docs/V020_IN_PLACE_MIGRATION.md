# v0.2.0 in-place module migration

The ColorOS 17 clean branch keeps the legacy module ID:

`material_you_for_coloros`

This is intentional. Installing v0.2.0 replaces the old v0.1.4 payload instead of mounting two competing systemless overlay modules at the same time.

The new payload does **not** carry forward the legacy package-wide geometry/surface overrides. The old files disappear when the module directory is replaced.

State used by the new clean implementation remains under `/data/adb/coloros-monet` and is recreated/extended safely by the installer.

Legacy SystemUI single/dual + blur/monet APK switching is not implicitly preserved because those old APKs are part of the architecture being retired. Equivalent ColorOS 17 behavior must be reintroduced as narrowly scoped components, not by copying the old global overlays.
