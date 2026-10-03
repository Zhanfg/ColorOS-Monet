# Retired Android 17 generic artwork path

The v0.1.5 compatibility experiment generated generic 24dp line icons and broad package-wide color/shape replacements.

That path is intentionally removed from the v0.2.0 branch.

## Why

ColorOS 17 uses vendor-specific geometry, alpha layering, blur/translucency and component structure. Generic replacement artwork can look superficially Material while being visually and structurally wrong.

The v0.2.0 rule is:

- preserve target icon/vector geometry;
- never synthesize a generic replacement for a vendor drawable;
- allow semantic tint only when the component role is known;
- derive migrations from a user-supplied local target dump when a resource was renamed;
- keep proprietary artwork out of the public repository.

The old v0.1.5 branch remains the historical record of that experiment. It is not part of the v0.2.0 shipping path.
