#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations
import argparse, hashlib, json, struct
from pathlib import Path

MAGIC=b"CMONET01"; HEADER=128

def audit(path:Path)->dict:
    data=path.read_bytes()
    if len(data)<HEADER or data[:8]!=MAGIC: raise ValueError(f"{path}: bad magic/header")
    version,header_size=struct.unpack_from('<HH',data,8)
    flags=struct.unpack_from('<I',data,12)[0]
    manifest_len,payload_len=struct.unpack_from('<QQ',data,16)
    if version!=1 or header_size!=HEADER or flags&1==0: raise ValueError(f"{path}: unsupported header")
    if any(data[96:128]): raise ValueError(f"{path}: nonzero reserved header")
    if len(data)!=HEADER+manifest_len+payload_len: raise ValueError(f"{path}: length mismatch")
    manifest=data[HEADER:HEADER+manifest_len]; payload=data[HEADER+manifest_len:]
    if hashlib.sha256(manifest).digest()!=data[32:64]: raise ValueError(f"{path}: manifest digest")
    if hashlib.sha256(payload).digest()!=data[64:96]: raise ValueError(f"{path}: payload digest")
    meta=json.loads(manifest)
    if meta.get('backend')!='fabricated-overlay': raise ValueError(f"{path}: unexpected backend")
    return {'file':path.name,'id':meta['id'],'target':meta['target_package'],'bytes':len(data)}

def main()->int:
    p=argparse.ArgumentParser();p.add_argument('paths',nargs='+',type=Path);args=p.parse_args()
    files=[]
    for item in args.paths:
        files.extend(sorted(item.glob('*.cmonet')) if item.is_dir() else [item])
    reports=[audit(f) for f in files]
    if len({r['id'] for r in reports})!=len(reports): raise ValueError('duplicate component IDs')
    print(json.dumps(reports,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
