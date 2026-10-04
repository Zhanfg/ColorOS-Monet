# MD3E / Expressive upstream manifest

The project now pins four distinct upstream ownership families rather than
treating "Material" as one undifferentiated source.

## 1. ColorOS native resources

These remain the first source whenever the current ROM already wires the
resource/component correctly.

## 2. Android 17 Settings / SettingsLib / SystemUI

Pinned AOSP release references define the component-level Expressive behavior
and the native Settings gate/group/icon treatment.

## 3. Android 17 SetupDesign

Pinned separately because `sud_*` / Glif resources are not SettingsLib and
must not be routed into generic Material Symbol matching.

## 4. Google Material Symbols

Pinned generic glyph catalog for real semantic gaps.

The canonical revision set is in:

`compat/material-symbols/upstream_manifest.lock`

CI cross-checks the manifest against the individual source locks so one upstream
cannot drift silently while another remains pinned.
