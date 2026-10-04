# AOSP Expressive extraction tooling

The project now has a reproducible way to analyze a local checkout of AOSP
Settings rather than relying on manually copied resource names.

`tools/extract_aosp_expressive_wrappers.py` scans the Settings resources and:

- identifies drawable XML whose resource name contains `expressive`;
- detects `TintDrawable` wrappers;
- extracts the wrapped base drawable;
- extracts the tint color role;
- records XML consumers that reference each Expressive drawable.

`tools/compare_coloros_aosp_expressive.py` then compares that public AOSP
inventory against the derived ColorOS 17 Expressive resource inventory.

This is intentionally resource-level analysis only. It does not replace the
Codex runtime consumer trace for ColorOS.
