# OPlus Settings homepage Material Symbols review pack

The OPlus homepage currently exposes a small set of generic semantic gaps where a native `*_expressive` wrapper has not been proven.

Current candidate rows include generic concepts such as:

- airplane mode;
- Wi-Fi;
- Bluetooth settings;
- screen lock;
- accounts;
- legal information.

CI builds a **non-flashable review pack** from the pinned Google Material Symbols revision.

The pack preserves, in metadata:

- OPlus preference key/class;
- current vendor icon resource name;
- controller;
- native two-tone tint category;
- Material Symbol family/size/ref/hash.

It intentionally does not include or redistribute vendor drawables.

Purpose: review exact official glyph geometry before any runtime/RRO experiment. A candidate remains a candidate until the OPlus two-tone consumer is verified on-device.
