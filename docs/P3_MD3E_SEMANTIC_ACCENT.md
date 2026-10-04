# P3: conservative MD3E semantic accent layer

The resource classifier reduced the legacy v0.1.4 color overrides to a small set of high-confidence accent roles that still exist on the current ColorOS 17 targets.

The first conservative layer contains **106 locally proven target color resources across 14 packages**.

The retained resource family is intentionally narrow:

- `coui_color_blue`
- `coui_color_primary_blue`
- `coui_color_primary_on_popup_blue`
- `coui_color_primary_text_blue`
- `coui_color_additional_blue`
- `coui_color_blue`
- `colorPrimary` where it exists and was already part of the legacy semantic mapping

All map to Android/ColorOS' active `system_primary_light/dark` role.

## What is deliberately excluded

- neutral surfaces;
- card/background colors;
- dividers;
- press/disabled/state colors;
- typography colors that merely contain the word "primary";
- geometry;
- vendor drawables/icons.

Those remain native until a component-specific rule exists.

This is the first layer that can replace a large portion of the legacy "make everything Material" strategy with a small semantic contract that follows the ROM's own Monet palette.
