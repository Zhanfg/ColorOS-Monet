# ColorOS 17 semantic-accent provenance

The v0.2.0 semantic table is deliberately evidence-based rather than name-only.

For the current PJZ110 ColorOS 17 snapshot, the local verifier cross-checks every shipping row against three independent facts:

1. the resource exists in the current ColorOS 17 target package;
2. the same resource existed in the legacy v0.1.4 overlay for that target;
3. the legacy light/night values resolve exactly to the current framework IDs for
   `system_primary_light` and `system_primary_dark`.

## Current verified set

- **106 / 106** shipping semantic rows satisfy all three checks.
- They span **14 target packages**.
- No surface/background/divider/press/geometry resource is admitted by the shipping-policy linter.

The additional common COUI family verified in this pass is:

- `coui_color_container_theme_blue`
- `coui_color_label_theme_blue`
- `coui_color_tips`

These exist in the current targets and were explicitly mapped by the legacy module to the same Android system-primary pair. They are therefore treated as accent-semantic roles rather than inferred from their names alone.

## Reproducibility

Run locally with the user-supplied files:

```sh
python tools/verify_coloros17_semantic_local.py \
  --aapt2 /path/to/aapt2 \
  --legacy-overlay-dir /path/to/v0.1.4/system/product/overlay \
  --target-dump-dir /path/to/ColorOS17_TargetDump/files/targets \
  --framework-res /path/to/framework-res.apk
```

Vendor APKs and resource payloads are intentionally not committed to the public repository.
