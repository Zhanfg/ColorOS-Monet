# Native Expressive provenance closure

The earlier `native_expressive_unmatched.tsv` list meant only that no trivial
same-package base resource was found by removing the word `expressive`. It did
**not** mean those resources lacked a public Android 17 origin.

This pass joins that list against the pinned Android 17 upstream overlap table.

## Result

- unmatched ColorOS named Expressive rows: **73**
- exact Android 17 name matches: **67**
- rows without an exact Android 17 Settings/SettingsLib/SystemUI/Core match: **6**

The machine-readable result is:

`compat/material-symbols/native_expressive_provenance.tsv`

This gives us three distinct evidence classes:

1. **native sibling pair** — ColorOS contains both base and Expressive resource;
2. **Android 17 upstream exact-name match** — ColorOS resource is structurally
   traceable to pinned AOSP Settings/SettingsLib/SystemUI/Core;
3. **ColorOS-only Expressive name** — preserve native and require consumer
   evidence; never invent a Material Symbol replacement merely from the name.

## Why this matters

The icon/component source resolver can now avoid sending already-proven Android
17 Expressive resources to the generic Material Symbols matcher.

Material Symbols remains the fallback for genuine generic glyph gaps, not the
primary source for assets ColorOS already inherited from Android 17.
