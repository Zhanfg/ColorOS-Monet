# Material Symbols state-axis validation

A Material Symbol exposing a `fill1` file does **not** guarantee that the selected glyph is visually different from the base glyph.

The pinned OPlus Settings homepage review pack proves this directly for the six current generic candidates:

| key | symbol | fill1 changes XML? | policy |
|---|---|---:|---|
| airplane_mode | flight | no | static glyph only |
| wifi_settings | wifi | no | static glyph only |
| bluetooth_settings | settings_bluetooth | no | static glyph only |
| screen_lock | lock | yes | stateful candidate |
| account_settings | manage_accounts | yes | stateful candidate |
| legal_information | gavel | no | static glyph only |

Therefore `base -> fill1` must never be assumed merely because both files exist.

The CI-generated file `material-symbols-state-deltas.tsv` compares the exact pinned XML bytes used by the review pack. A mapping may become `STATEFUL_SYMBOL` only when:

1. the consumer itself has a selected/unselected state;
2. the pinned upstream selected asset exists;
3. the selected XML differs from the base XML;
4. visual review confirms that the state transition is appropriate in the ColorOS component.

Otherwise the Material Symbol is treated as a static glyph and ColorOS/OPlus remains the state/tint owner.
