# Native Expressive provenance closure

The earlier `native_expressive_unmatched.tsv` list meant only that no trivial
same-package base resource was found by removing the word `expressive`. It did
**not** mean those resources lacked a public Android 17 origin.

This pass joins that list against the pinned Android 17 upstream overlap table.

## Result

- unmatched ColorOS named Expressive rows: **73**
- exact Android 17 name matches: **67**
- exact SetupDesign Expressive-family matches: **4**
- ColorOS target-XML verified extensions: **2**
- unresolved provenance rows: **0**

The machine-readable result is:

`compat/material-symbols/native_expressive_provenance.tsv`

This gives us three distinct evidence classes:

1. **native sibling pair** — ColorOS contains both base and Expressive resource;
2. **Android 17 upstream exact-name match** — ColorOS resource is structurally
   traceable to pinned AOSP Settings/SettingsLib/SystemUI/Core;
3. **SetupDesign Expressive family** — public SetupDesign confirms the checked
   selector family even when the resource is outside Settings/SettingsLib.
4. **ColorOS verified extension** — the current target APK itself proves the
   additional state asset and selector binding. Preserve it natively; do not
   substitute a Material Symbol.

## Why this matters

The icon/component source resolver can now avoid sending already-proven Android
17 Expressive resources to the generic Material Symbols matcher.

Material Symbols remains the fallback for genuine generic glyph gaps, not the
primary source for assets ColorOS already inherited from Android 17.


## ColorOS unchecked-switch extension

The two previously unresolved resources are now closed using the user's current
ColorOS 17 Settings/SystemUI APKs.

Both packages define `sud_ic_switch_uncheck_mark_expressive` as a 16dp vector
cross glyph. Their native `sud_ic_switch_selector_expressive` selects:

- the public-family checked-mark asset for `state_checked=true`;
- the ColorOS cross asset for `state_checked=false`.

This is a deliberate ColorOS state extension, not a missing Google/Material
glyph. It is therefore `KEEP_NATIVE`.

No vendor path data is stored in this repository.
