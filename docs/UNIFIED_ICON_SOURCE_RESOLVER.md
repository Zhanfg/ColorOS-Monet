# Unified icon-source resolver

The ColorOS 17 icon resolver now records both the selected asset and its
upstream/native ownership.

For each candidate it emits:

- preferred source;
- selected native asset or Material Symbol;
- runtime/review gate;
- Material Symbol fallback;
- upstream owner;
- provenance status;
- upstream path where applicable.

Recognized ownership families include:

- ColorOS native;
- Android 17 Settings / SettingsLib;
- Android 17 SetupDesign/Glif;
- Google Material Symbols.

This prevents a native Expressive/SUD asset from being silently treated as a
generic Material Symbol merely because both represent the same concept.

CI verifies the pinned SetupDesign release and produces a resolved source table
as a build artifact.
