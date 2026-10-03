#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import shutil
import struct
import subprocess
import tempfile
import zipfile
import zlib
from pathlib import Path

TARGET_METHODS = {
    ("Lone/dot/couiexpressive/hooks/widget/CardHook;", "handleLoadPackage"),
    ("Lone/dot/couiexpressive/hooks/widget/ListHook;", "handleLoadPackage"),
}

def u16(buf: bytes | bytearray, off: int) -> int:
    return struct.unpack_from("<H", buf, off)[0]

def u32(buf: bytes | bytearray, off: int) -> int:
    return struct.unpack_from("<I", buf, off)[0]

def uleb(buf: bytes | bytearray, off: int) -> tuple[int, int]:
    value = 0
    shift = 0
    i = off
    while True:
        b = buf[i]
        i += 1
        value |= (b & 0x7F) << shift
        if b < 0x80:
            return value, i
        shift += 7
        if shift > 35:
            raise ValueError("invalid uleb128")

def dex_tables(buf: bytes | bytearray):
    string_size, string_off = u32(buf, 0x38), u32(buf, 0x3C)
    type_size, type_off = u32(buf, 0x40), u32(buf, 0x44)
    proto_size, proto_off = u32(buf, 0x48), u32(buf, 0x4C)
    method_size, method_off = u32(buf, 0x58), u32(buf, 0x5C)
    class_size, class_off = u32(buf, 0x60), u32(buf, 0x64)

    strings: list[str] = []
    for i in range(string_size):
        off = u32(buf, string_off + i * 4)
        _, p = uleb(buf, off)
        e = buf.index(0, p)
        strings.append(bytes(buf[p:e]).decode("utf-8", "replace"))

    types = [strings[u32(buf, type_off + i * 4)] for i in range(type_size)]

    protos: list[tuple[str, list[str]]] = []
    for i in range(proto_size):
        q = proto_off + i * 12
        return_type = u32(buf, q + 4)
        params_off = u32(buf, q + 8)
        params: list[str] = []
        if params_off:
            n = u32(buf, params_off)
            params = [types[u16(buf, params_off + 4 + j * 2)] for j in range(n)]
        protos.append((types[return_type], params))

    methods = []
    for i in range(method_size):
        q = method_off + i * 8
        methods.append(
            (
                types[u16(buf, q)],
                strings[u32(buf, q + 4)],
                protos[u16(buf, q + 2)],
            )
        )

    class_data = {}
    for i in range(class_size):
        q = class_off + i * 32
        class_data[types[u32(buf, q)]] = u32(buf, q + 24)

    return methods, class_data

def patch_dex(raw: bytes) -> tuple[bytes, list[tuple[str, str, int, int]]]:
    buf = bytearray(raw)
    methods, classes = dex_tables(buf)
    patched: list[tuple[str, str, int, int]] = []

    for class_name, method_name in TARGET_METHODS:
        class_data_off = classes.get(class_name)
        if not class_data_off:
            raise RuntimeError(f"class not found: {class_name}")

        p = class_data_off
        static_fields, p = uleb(buf, p)
        instance_fields, p = uleb(buf, p)
        direct_methods, p = uleb(buf, p)
        virtual_methods, p = uleb(buf, p)

        for _ in range(static_fields + instance_fields):
            _, p = uleb(buf, p)
            _, p = uleb(buf, p)

        found = False
        for count in (direct_methods, virtual_methods):
            method_idx = 0
            for _ in range(count):
                diff, p = uleb(buf, p)
                _, p = uleb(buf, p)
                code_off, p = uleb(buf, p)
                method_idx += diff

                owner, name, proto = methods[method_idx]
                if owner != class_name or name != method_name or proto[0] != "V":
                    continue
                if not code_off:
                    raise RuntimeError(f"method has no code item: {class_name}->{method_name}")

                insns_size = u32(buf, code_off + 12)
                if insns_size < 1:
                    raise RuntimeError(f"empty code item: {class_name}->{method_name}")

                insns_off = code_off + 16
                struct.pack_into("<H", buf, insns_off, 0x000E)  # return-void
                for i in range(1, insns_size):
                    struct.pack_into("<H", buf, insns_off + i * 2, 0x0000)  # nop

                patched.append((class_name, method_name, code_off, insns_size))
                found = True

        if not found:
            raise RuntimeError(f"method not found: {class_name}->{method_name}")

    # DEX integrity fields.
    buf[12:32] = hashlib.sha1(buf[32:]).digest()
    struct.pack_into("<I", buf, 8, zlib.adler32(buf[12:]) & 0xFFFFFFFF)
    return bytes(buf), patched

def run(*args: object) -> None:
    cmd = [str(x) for x in args]
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Patch COE 2.9.3 for ColorOS 17 native-first P0 by disabling only global CardHook/ListHook entry points."
    )
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--apksigner", type=Path, required=True)
    ap.add_argument("--keystore", type=Path, required=True)
    ap.add_argument("--zipalign", type=Path)
    args = ap.parse_args()

    with zipfile.ZipFile(args.input) as src:
        original_dex = src.read("classes.dex")
        patched_dex, patched = patch_dex(original_dex)

        with tempfile.TemporaryDirectory(prefix="coe-nativefirst-p0-") as td:
            work = Path(td)
            unsigned = work / "unsigned.apk"
            aligned = work / "aligned.apk"

            with zipfile.ZipFile(unsigned, "w") as out:
                for info in src.infolist():
                    upper = info.filename.upper()
                    if upper.startswith("META-INF/") and upper.endswith((".RSA", ".DSA", ".EC", ".SF")):
                        continue
                    payload = patched_dex if info.filename == "classes.dex" else src.read(info.filename)
                    clone = zipfile.ZipInfo(info.filename, date_time=info.date_time)
                    clone.compress_type = info.compress_type
                    clone.external_attr = info.external_attr
                    clone.flag_bits = info.flag_bits & ~0x08
                    out.writestr(clone, payload)

            signing_input = unsigned
            if args.zipalign:
                try:
                    run(args.zipalign, "-f", "4", unsigned, aligned)
                    signing_input = aligned
                except subprocess.CalledProcessError:
                    print("! zipalign unavailable; signing rebuilt APK without zipalign")

            args.output.parent.mkdir(parents=True, exist_ok=True)
            run(
                args.apksigner,
                "sign",
                "--ks", args.keystore,
                "--ks-pass", "pass:android",
                "--ks-key-alias", "androiddebugkey",
                "--key-pass", "pass:android",
                "--out", args.output,
                signing_input,
            )
            run(args.apksigner, "verify", "--verbose", args.output)

    print("patched entry points:")
    for item in patched:
        print(" ", item)
    print("sha256", hashlib.sha256(args.output.read_bytes()).hexdigest())
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
