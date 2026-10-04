# Complete ColorOS 17 named Expressive provenance

The current PJZ110 ColorOS 17 target snapshot contains **133** drawable/mipmap
resource-table entries whose names include `expressive`. That raw count also
includes generated animation-frame internals.

After excluding generated/internal frame names, the project tracks **109 named
Expressive resources** across framework, Settings and SystemUI.

## Provenance closure

All **109 / 109** named resources now have an exact public Android 17 upstream
owner:

- **103** package/resource rows: exact-name matches in pinned Android 17
  Settings / SettingsLib / SystemUI / framework sources;
- **6** package/resource rows: the three SetupDesign/Glif Expressive switch
  resources present in both Settings and SystemUI, verified from the pinned
  Android 17 SetupDesign release.

There are currently **zero named Expressive resources in this audited set whose
origin requires guessing or a Material Symbol approximation**.

Machine-readable table:

`compat/material-symbols/native_expressive_full_provenance.tsv`

## Consequence

For a resource that already appears in this table, Google Material Symbols is
not its source. Material Symbols may remain a semantic fallback/reference, but
the preferred implementation path is the existing ColorOS resource and its
verified Android 17 component owner.

This makes the source hierarchy concrete:

```text
current ColorOS Expressive resource
        -> exact Android 17 component upstream
        -> preserve native consumer/geometry
        -> Material Symbols only for a genuine missing generic glyph
```

The old `native_expressive_provenance.tsv` covered only the previously
"unmatched-base-name" subset. The full table supersedes it for source
resolution.
