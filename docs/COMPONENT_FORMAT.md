# `.cmonet` component format

## Goals

- recognizable by a WebUI without unpacking arbitrary ZIP files;
- deterministic validation before installation;
- no APK container requirement;
- explicit backend and target metadata;
- safe extraction with bounded lengths and path checks.

## Header

All integer fields are little-endian.

| Offset | Size | Field |
|---:|---:|---|
| `0x00` | 8 | ASCII magic `CMONET01` |
| `0x08` | 2 | format version, currently `1` |
| `0x0A` | 2 | header size, currently `128` |
| `0x0C` | 4 | flags; bit 0 means zstd-compressed tar payload |
| `0x10` | 8 | UTF-8 manifest length |
| `0x18` | 8 | payload length |
| `0x20` | 32 | SHA-256 manifest digest |
| `0x40` | 32 | SHA-256 payload digest |
| `0x60` | 32 | reserved; all bytes must be zero |

The file layout is:

```text
[128-byte header][component.json bytes][compressed tar payload]
```

## Manifest

Required fields:

```json
{
  "schema": 1,
  "id": "tim-monet",
  "name": "TIM Monet",
  "version": "0.2.0",
  "target_package": "com.tencent.tim",
  "overlay_name": "coloros_monet_tim",
  "backend": "fabricated-overlay",
  "resources": "resources.tsv"
}
```

Optional WebUI-facing fields include `category`, `tags`, `description`, `inspiration`, `exclusive_group`, `default_enabled`, `min_sdk`, and `source_status`.

## Resource table

`resources.tsv` uses four columns:

```text
type<TAB>resource_name<TAB>value<TAB>configuration
```

Supported values include:

- `@android:color/system_primary_light`
- `argb:ff112233`
- `string:Text`
- `file:compiled-assets/drawable-....xml`
- boolean, integer, and dimension literals.

## Safety rules

- package and payload lengths are bounded;
- both payload sections must match their SHA-256 values;
- absolute paths, `..`, symlinks, hardlinks, and special archive entries are rejected;
- component IDs, versions, package names, and overlay names are validated;
- installation uses a staging directory and atomic rename;
- components cannot execute scripts from their payload.
