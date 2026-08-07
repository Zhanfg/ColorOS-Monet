#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations
import argparse, shutil, stat, tempfile, zipfile
from pathlib import Path

EXECUTABLES={"customize.sh","service.sh","post-fs-data.sh","action.sh","uninstall.sh","bin/monetctl","META-INF/com/google/android/update-binary"}

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,default=Path.cwd())
    p.add_argument('--runtime',type=Path,required=True)
    p.add_argument('--components',type=Path,default=Path('build/components'))
    p.add_argument('--version',required=True);p.add_argument('--version-code',required=True,type=int)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();root=a.root.resolve()
    runtime=a.runtime.resolve();components=(root/a.components).resolve() if not a.components.is_absolute() else a.components
    if not runtime.is_file():raise FileNotFoundError(runtime)
    packages=sorted(components.glob('*.cmonet'))
    if not packages:raise RuntimeError('no .cmonet components')
    with tempfile.TemporaryDirectory(prefix='coloros-monet-v2-') as td:
        stage=Path(td)/'module';shutil.copytree(root/'module',stage)
        prop=(stage/'module.prop.in').read_text(encoding='utf-8')
        prop=prop.replace('@VERSION@',a.version).replace('@VERSION_CODE@',str(a.version_code))
        (stage/'module.prop').write_text(prop,encoding='utf-8');(stage/'module.prop.in').unlink()
        (stage/'bin').mkdir(exist_ok=True);shutil.copy2(runtime,stage/'bin/monetctl')
        dest=stage/'components';dest.mkdir(exist_ok=True)
        for pkg in packages:shutil.copy2(pkg,dest/pkg.name)
        # Do not ship obsolete static RRO payloads.
        shutil.rmtree(stage/'payload',ignore_errors=True)
        a.output.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(a.output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for path in sorted(stage.rglob('*')):
                if not path.is_file():continue
                rel=path.relative_to(stage).as_posix();info=zipfile.ZipInfo(rel)
                info.date_time=(2026,1,1,0,0,0)
                mode=0o755 if rel in EXECUTABLES else 0o644
                info.external_attr=(stat.S_IFREG|mode)<<16
                z.writestr(info,path.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    print(f'packed {len(packages)} components -> {a.output}')
    return 0
if __name__=='__main__':raise SystemExit(main())
