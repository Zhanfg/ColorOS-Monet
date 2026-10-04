#!/usr/bin/env python3
from __future__ import annotations

import argparse
import struct
import zipfile
from pathlib import Path

TARGETS = {
    "Lcom/oplus/settings/widget/preference/SettingJumpPreference;",
    "Lcom/oplus/settings/widget/preference/SettingsSimpleJumpPreference;",
    "Lcom/oplus/settings/widget/preference/SettingsCornerMarkPreference;",
    "Lcom/oplus/settings/widget/preference/SettingsRedDotPreference;",
    "Lcom/oplus/settings/widget/preference/SettingSwitchPreference;",
    "Lcom/oplus/settings/widget/preference/SettingsAirPlaneSwitchPreference;",
}

def uleb(data: bytes, off: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while True:
        b = data[off]
        off += 1
        value |= (b & 0x7F) << shift
        if b < 0x80:
            return value, off
        shift += 7

def parse_dex(data: bytes):
    u16 = lambda off: struct.unpack_from("<H", data, off)[0]
    u32 = lambda off: struct.unpack_from("<I", data, off)[0]

    string_size, string_off = u32(0x38), u32(0x3C)
    type_size, type_off = u32(0x40), u32(0x44)
    field_size, field_off = u32(0x50), u32(0x54)
    method_size, method_off = u32(0x58), u32(0x5C)
    class_size, class_off = u32(0x60), u32(0x64)

    strings = []
    for i in range(string_size):
        off = u32(string_off + i * 4)
        _, p = uleb(data, off)
        end = data.index(0, p)
        strings.append(data[p:end].decode("utf-8", "replace"))

    types = [strings[u32(type_off + i * 4)] for i in range(type_size)]

    fields = []
    for i in range(field_size):
        q = field_off + i * 8
        fields.append((
            types[u16(q)],
            strings[u32(q + 4)],
            types[u16(q + 2)],
        ))

    methods = []
    for i in range(method_size):
        q = method_off + i * 8
        methods.append((
            types[u16(q)],
            strings[u32(q + 4)],
        ))

    classes = {}
    for i in range(class_size):
        q = class_off + i * 32
        cidx = u32(q)
        sidx = u32(q + 8)
        classes[types[cidx]] = {
            "super": None if sidx == 0xFFFFFFFF else types[sidx],
            "data_off": u32(q + 24),
        }

    return fields, methods, classes

def members(data: bytes, fields, methods, info):
    off = info["data_off"]
    if not off:
        return [], []

    static_fields, off = uleb(data, off)
    instance_fields, off = uleb(data, off)
    direct_methods, off = uleb(data, off)
    virtual_methods, off = uleb(data, off)

    out_fields = []
    idx = 0
    for _ in range(static_fields + instance_fields):
        diff, off = uleb(data, off)
        _, off = uleb(data, off)
        idx += diff
        out_fields.append(fields[idx][1])

    out_methods = []
    idx = 0
    for count in (direct_methods, virtual_methods):
        idx = 0
        for _ in range(count):
            diff, off = uleb(data, off)
            _, off = uleb(data, off)
            _, off = uleb(data, off)
            idx += diff
            out_methods.append(methods[idx][1])

    return out_fields, out_methods

def human(desc: str | None) -> str:
    if not desc:
        return ""
    if desc.startswith("L") and desc.endswith(";"):
        return desc[1:-1].replace("/", ".")
    return desc

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--settings-apk", type=Path, required=True)
    args = p.parse_args()

    found = {}
    with zipfile.ZipFile(args.settings_apk) as apk:
        dex_names = sorted(
            n for n in apk.namelist()
            if n == "classes.dex" or (
                n.startswith("classes") and n.endswith(".dex")
                and n[7:-4].isdigit()
            )
        )
        for dex_name in dex_names:
            data = apk.read(dex_name)
            fields, methods, classes = parse_dex(data)
            for target in TARGETS:
                if target not in classes or target in found:
                    continue
                fs, ms = members(data, fields, methods, classes[target])
                found[target] = (
                    dex_name,
                    human(classes[target]["super"]),
                    fs,
                    ms,
                )

    for target in sorted(TARGETS):
        if target not in found:
            print(f"MISSING\t{human(target)}")
            continue
        dex_name, superclass, fs, ms = found[target]
        print(
            "\t".join([
                human(target),
                superclass,
                ";".join(fs),
                ";".join(ms),
                dex_name,
            ])
        )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
