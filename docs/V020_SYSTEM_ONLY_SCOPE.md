# v0.2.0 system-only shipping scope

The ColorOS 17 v0.2.0 branch ships only ColorOS/system visual integration.

The older clean-room repository also contains optional X, TIM and Coolapk overlays, but those are deliberately excluded from the v0.2.0 ColorOS module.

Reasons:

- the user goal is a coherent ColorOS 17 design system;
- third-party app resources have independent release/version compatibility;
- they should not increase the blast radius of a system visual module;
- they can be maintained as separate optional packages later.

The shipping module therefore contains the ColorOS 17 semantic accent layer and runtime helpers only. No unrelated application overlay is enabled or installed by default.
