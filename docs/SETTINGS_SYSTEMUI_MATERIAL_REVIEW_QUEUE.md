# Settings/SystemUI deterministic Material Symbol review queue

The full ColorOS 17 inventory currently yields **418 deterministic**
Material-Symbol name candidates across 26 packages.

For the two primary v0.2.0 system surfaces:

- Settings: **100** deterministic candidates;
- SystemUI: **62** deterministic candidates.

Before any Google glyph is reviewed, the candidate list is joined against the
current ROM's native Expressive resources.

Current result:

- Settings: **15** deterministic candidates already have a direct native
  Expressive sibling and therefore move to `PREFER_NATIVE_EXPRESSIVE`;
- Settings: **85** remain `MATERIAL_SYMBOL_REVIEW`;
- SystemUI: **62** remain `MATERIAL_SYMBOL_REVIEW` under the strict direct-
  sibling test.

That leaves **147** Settings/SystemUI generic candidates for later consumer-level
review, not 162 blind substitutions.

## Reproduce

Generate the private local inventories from the target dump, then run:

```sh
python tools/prioritize_material_candidates.py \
  --candidates /tmp/coloros17-deterministic-material.tsv \
  --expressive-inventory /tmp/coloros17-expressive-inventory.tsv \
  --package com.android.settings \
  --package com.android.systemui \
  --output /tmp/settings-systemui-material-review.tsv
```

## Important limitation

This direct-sibling pass is intentionally conservative. A missing
`<base>_expressive` sibling does **not** authorize a Material Symbol.

The next gates remain:

1. exact component consumer;
2. AOSP/ColorOS Expressive provenance under a different resource name;
3. state-machine ownership;
4. optical-size/tint compatibility;
5. only then a Material Symbol probe.

SystemUI candidates remain frozen until the Codex-required runtime component
binding is collected for QS/notification/media/volume/clock.
