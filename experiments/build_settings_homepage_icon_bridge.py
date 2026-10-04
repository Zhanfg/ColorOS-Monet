#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import subprocess
import tempfile
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "compat/material-symbols/settings_homepage_full_source_map.tsv"
LOCK = ROOT / "compat/material-symbols/upstream.lock"
FAMILY = "materialsymbolsrounded"
SIZE = "24"

ANDROID_NS = "http://schemas.android.com/apk/res/android"
ET.register_namespace("android", ANDROID_NS)

def run(*args: object) -> None:
    cmd=[str(x) for x in args]
    print("+"," ".join(cmd))
    subprocess.run(cmd,check=True)

def rows(path: Path) -> list[dict[str,str]]:
    with path.open(encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f,delimiter="\t"))

def target_drawables(aapt2: Path, settings_apk: Path) -> set[str]:
    text=subprocess.run(
        [str(aapt2),"dump","resources","--no-values",str(settings_apk)],
        check=True,text=True,stdout=subprocess.PIPE
    ).stdout
    out=set()
    for line in text.splitlines():
        line=line.strip()
        if " drawable/" not in line or not line.startswith("resource "):
            continue
        name=line.rsplit(" drawable/",1)[1].removesuffix(" PUBLIC")
        out.add(name)
    return out

def lock_values(path: Path) -> dict[str,str]:
    out={}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        k,v=line.split("=",1)
        out[k.strip()]=v.strip()
    return out

def drawable_name(value: str) -> str:
    value=value.strip()
    for prefix in ("drawable/","@drawable/"):
        if value.startswith(prefix):
            return value[len(prefix):]
    return value

def vector_source(upstream: Path, symbol: str) -> Path:
    name=f"{symbol}_{SIZE}px.xml"
    p=upstream/"symbols"/"android"/symbol/FAMILY/name
    if not p.is_file():
        raise RuntimeError(f"missing pinned Material Symbol: {p}")
    return p

def sanitize_vector(source: Path) -> bytes:
    # Preserve Google's official path geometry while removing palette ownership
    # from the copied probe asset. OPlus preference classes remain responsible
    # for runtime tint/two-tone treatment.
    root=ET.fromstring(source.read_bytes())
    if root.tag != f"{{{ANDROID_NS}}}vector":
        raise RuntimeError(f"not a VectorDrawable: {source}")

    tint_attr=f"{{{ANDROID_NS}}}tint"
    if tint_attr in root.attrib:
        # Material Symbols Android XML normally uses ?attr/colorControlNormal.
        # The probe must not import that theme ownership into ColorOS.
        root.attrib.pop(tint_attr)

    color_attrs={
        f"{{{ANDROID_NS}}}fillColor",
        f"{{{ANDROID_NS}}}strokeColor",
    }
    for node in root.iter():
        for attr,value in list(node.attrib.items()):
            if attr in color_attrs and value=="@android:color/white":
                node.attrib[attr]="#FFFFFFFF"
                continue
            if value.startswith("@") or value.startswith("?"):
                raise RuntimeError(
                    f"unexpected external resource reference {attr}={value} in {source}"
                )
    return ET.tostring(root,encoding="utf-8",xml_declaration=True)

def main() -> int:
    p=argparse.ArgumentParser(
        description="Build an experiment-only Settings homepage icon bridge."
    )
    p.add_argument("--aapt2",type=Path,required=True)
    p.add_argument("--framework-res",type=Path,required=True)
    p.add_argument("--settings-apk",type=Path,required=True)
    p.add_argument("--material-upstream",type=Path,required=True)
    p.add_argument("--mode",choices=("native","material","combined"),default="combined")
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--package",default="dev.zhanfg.coloros17.experiment.settingsiconbridge")
    p.add_argument("--version-code",type=int,default=26100420)
    p.add_argument("--version-name",default="0.2.0-settings-icon-bridge-exp1")
    args=p.parse_args()

    lock=lock_values(LOCK)
    pinned=lock.get("ref","")
    git_head=subprocess.run(
        ["git","-C",str(args.material_upstream),"rev-parse","HEAD"],
        text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL
    ).stdout.strip()
    if git_head and pinned and git_head != pinned:
        raise RuntimeError(f"Material Symbols checkout mismatch: {git_head} != {pinned}")

    selected=[]
    with tempfile.TemporaryDirectory(prefix="cos17-settings-icon-bridge-") as td:
        work=Path(td)
        values=work/"res"/"values"
        drawables=work/"res"/"drawable"
        values.mkdir(parents=True)
        drawables.mkdir(parents=True)

        aliases=['<?xml version="1.0" encoding="utf-8"?>',"<resources>"]
        available=target_drawables(args.aapt2,args.settings_apk)

        for row in rows(MAP):
            source_kind=row["preferred_source"]
            source=drawable_name(row["current_icon"])
            candidate=drawable_name(row["preferred_candidate"])

            if source not in available:
                raise RuntimeError(f"target drawable missing: {source} ({row['key']})")

            if source_kind=="NATIVE_EXPRESSIVE" and args.mode in ("native","combined"):
                if row["confidence"]!="HIGH":
                    continue
                if candidate not in available:
                    raise RuntimeError(
                        f"native Expressive candidate missing: {candidate} ({row['key']})"
                    )
                aliases.append(
                    f'    <item type="drawable" name="{source}">'
                    f'@*com.android.settings:drawable/{candidate}</item>'
                )
                selected.append((row["key"],source,candidate,"NATIVE_EXPRESSIVE"))
            elif source_kind=="MATERIAL_SYMBOL" and args.mode in ("material","combined"):
                if row["confidence"] not in ("HIGH","MEDIUM") or not candidate:
                    continue
                xml=vector_source(args.material_upstream,candidate)
                (drawables/f"{source}.xml").write_bytes(sanitize_vector(xml))
                selected.append((row["key"],source,candidate,"MATERIAL_SYMBOL"))

        aliases.append("</resources>")
        (values/"aliases.xml").write_text("\n".join(aliases)+"\n",encoding="utf-8")

        manifest=work/"AndroidManifest.xml"
        manifest.write_text(
            f'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="{args.package}"
    android:versionCode="{args.version_code}"
    android:versionName="{args.version_name}">
    <uses-sdk android:minSdkVersion="37" android:targetSdkVersion="37" />
    <application android:allowBackup="false" android:hasCode="false" />
    <overlay android:targetPackage="com.android.settings" android:isStatic="false" />
</manifest>
''',
            encoding="utf-8"
        )

        compiled=work/"compiled.zip"
        unsigned=work/"unsigned.apk"
        run(args.aapt2,"compile","--dir",work/"res","-o",compiled)
        run(
            args.aapt2,"link",
            "-o",unsigned,
            "-I",args.framework_res,
            "-I",args.settings_apk,
            "--manifest",manifest,
            "--auto-add-overlay",
            compiled,
        )
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_bytes(unsigned.read_bytes())

    print(f"mode={args.mode}")
    print(f"selected={len(selected)}")
    for key,source,target,kind in selected:
        print(f"{kind}\t{key}\t{source}\t{target}")
    print("NOTE=experiment-only unsigned RRO; not part of shipping module")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
