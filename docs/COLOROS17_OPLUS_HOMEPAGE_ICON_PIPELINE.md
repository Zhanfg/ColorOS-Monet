# ColorOS 17 OPlus Settings homepage icon pipeline

The full current Settings APK closes the main homepage XML evidence gap.

## Exact XML consumer

The launcher route reaches:

`OplusTopLevelSettings.getPreferenceScreenResId() -> res/xml/top_level_settings_oplus.xml`.

The XML contains **42 preferences with explicit icon resources**.

Observed summary:

- 42 icon-bearing homepage preferences;
- 41 set `showTwoToneColor=true`;
- 39 set `needChangeDrawType=true`;
- 41 point `tintIconNew` at `integer/tint_item_icon_ops`;
- the dominant `tintType` groups are blue, green, orange and yellow, with one red SOS item;
- **zero** of the 42 XML icon resources are named `*_expressive`.

The integer mapping in the current Settings resources is:

- `tint_icon_green = 0`
- `tint_icon_blue = 1`
- `tint_icon_orange = 2`
- `tint_icon_yellow = 3`
- `tint_icon_red = 4`
- `tint_item_icon_ops = 1`

## Architectural consequence

The OPlus Settings homepage is not simply an AOSP homepage whose XML can be swapped to `ic_settings_*_expressive`.

Its current icon contract is:

```text
top_level_settings_oplus.xml
    -> OPlus preference subclass
    -> vendor icon resource (settings_*_ic)
    -> showTwoToneColor / needChangeDrawType
    -> tintIconNew + tintType category
```

This is a native ColorOS icon-treatment pipeline.

Therefore:

1. do not replace all homepage icons with Material Symbols;
2. do not force `top_level_settings_expressive.xml`;
3. do not infer that the presence of `ic_settings_*_expressive` means the OPlus homepage consumes them;
4. keep the OPlus semantic glyph and two-tone category system as the default owner;
5. use native/AOSP Expressive or Material Symbols only for a specific glyph gap after the OPlus preference consumer is verified.

## Relation to the native Expressive adapter

This finding does **not** invalidate the native SettingsLib Expressive grouped-list path.

`OplusTopLevelSettings` still inherits the Settings preference-fragment stack, so the native
`SettingsPreferenceGroupAdapter` can own first/middle/last/single section geometry when the Settings Expressive gate is enabled.

That means the correct split is:

- **row/group geometry:** SettingsLib native Expressive path;
- **homepage icon semantics/two-tone categories:** OPlus homepage preference layer;
- **Monet accent values:** native active palette / verified semantic resources;
- **Material Symbols:** gap filler, not homepage-wide replacement.

## Reproducibility

Derived table:

`compat/coloros17/settings_oplus_homepage_icons.tsv`

Rebuild it from a user-supplied current Settings APK with:

```sh
python tools/extract_settings_oplus_homepage_icons.py \
  --aapt2 /path/to/aapt2 \
  --settings-apk /path/to/Settings.apk \
  --output /tmp/settings_oplus_homepage_icons.tsv
```

No vendor XML or drawable payload is stored in the public repository; only derived resource/controller metadata is committed.


## DEX ownership confirmation

The OPlus preference hierarchy itself declares the two-tone/tint state:
`SettingJumpPreference` owns `mShowTwoToneColor`, `mTintIcon`,
`mTintType` and `mNeedChangeCanvasType`, while its subclasses bind the
homepage rows. See `docs/COLOROS17_OPLUS_ICON_OWNER.md`.

This upgrades the homepage icon-owner conclusion from XML-only evidence to
XML + class-structure evidence.
