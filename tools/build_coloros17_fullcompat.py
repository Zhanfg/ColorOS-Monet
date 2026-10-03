#!/usr/bin/env python3
from __future__ import annotations
import argparse, os, re, shutil, subprocess, tempfile, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SDK_DIR="37.0"; BT="37.0.0"
TARGETS={
"securitypermission":("com.oplus.securitypermission",1,0,"permission"),
"accessibilityassistant":("com.coloros.accessibilityassistant",1,0,""),
"browser":("com.heytap.browser",1,0,""),
"battery":("com.oplus.battery",1,0,""),
"digitalwellbeing":("com.coloros.digitalwellbeing",1,0,""),
"contacts":("com.android.contacts",1,0,"contacts"),
"breeno":("com.heytap.speechassist",1,0,""),
"launcher":("com.android.launcher",1,1,"launcher"),
"systemui":("com.android.systemui",1,1,"systemui"),
"wirelesssettings":("com.oplus.wirelesssettings",1,0,"wireless"),
"camera":("com.oplus.camera",1,0,""),
"pscanvas":("com.oplus.pscanvas",1,0,""),
"childrenspace":("com.coloros.childrenspace",1,0,""),
"notificationmanager":("com.oplus.notificationmanager",1,0,""),
"carconnect":("com.oplus.ocar",1,0,""),
"settings":("com.android.settings",1,1,"settings"),
"securitycenter":("com.oplus.safecenter",1,0,""),
"phonemanager":("com.coloros.phonemanager",1,0,""),
"linker":("com.oplus.linker",1,0,""),
"assistiveball":("com.coloros.floatassistant",1,0,""),
"eyeprotect":("com.oplus.eyeprotect",0,0,"eyeprotect"),
"phone":("com.android.phone",0,0,"phone"),
}
M3=["background","error","error_container","inverse_on_surface","inverse_primary","inverse_surface","on_background","on_error","on_error_container","on_primary","on_primary_container","on_secondary","on_secondary_container","on_surface","on_surface_variant","on_tertiary","on_tertiary_container","outline","outline_variant","primary","primary_container","secondary","secondary_container","surface","surface_bright","surface_container","surface_container_high","surface_container_highest","surface_container_low","surface_container_lowest","surface_dim","surface_variant","tertiary","tertiary_container"]
M3FIX=["on_primary_fixed","on_primary_fixed_variant","on_secondary_fixed","on_secondary_fixed_variant","on_tertiary_fixed","on_tertiary_fixed_variant","primary_fixed","primary_fixed_dim","secondary_fixed","secondary_fixed_dim","tertiary_fixed","tertiary_fixed_dim"]
MAT=["Background","ControlActivated","ControlHighlight","ControlNormal","Error","ErrorContainer","ErrorDim","InverseOnSurface","InversePrimary","InverseSurface","OnBackground","OnError","OnErrorContainer","OnPrimary","OnPrimaryContainer","OnPrimaryFixed","OnPrimaryFixedVariant","OnSecondary","OnSecondaryContainer","OnSecondaryFixed","OnSecondaryFixedVariant","OnSurface","OnSurfaceVariant","OnTertiary","OnTertiaryContainer","OnTertiaryFixed","OnTertiaryFixedVariant","Outline","OutlineVariant","PaletteKeyColorError","PaletteKeyColorNeutral","PaletteKeyColorNeutralVariant","PaletteKeyColorPrimary","PaletteKeyColorSecondary","PaletteKeyColorTertiary","Primary","PrimaryContainer","PrimaryDim","PrimaryFixed","PrimaryFixedDim","Scrim","Secondary","SecondaryContainer","SecondaryDim","SecondaryFixed","SecondaryFixedDim","Shadow","Surface","SurfaceBright","SurfaceContainer","SurfaceContainerHigh","SurfaceContainerHighest","SurfaceContainerLow","SurfaceContainerLowest","SurfaceDim","SurfaceTint","SurfaceVariant","Tertiary","TertiaryContainer","TertiaryDim","TertiaryFixed","TertiaryFixedDim","TextHintInverse","TextPrimaryInverse","TextPrimaryInverseDisableOnly","TextSecondaryAndTertiaryInverse","TextSecondaryAndTertiaryInverseDisabled"]
CATS=["about","accessibility","accounts","apps","battery","connected_device","device","display","hub_mode","location","modes","network","notification","safety","security","sound","storage","supervision","support","system","wallpaper"]
SET_IC={"device_market_name_phone_icon":"phone","ic_device_cpu_card":"chip","ic_device_spec_card_placeholder":"memory","ic_device_info_camera_decor":"camera","ic_device_battery_trailing":"battery","ic_device_screen_info_card":"display","ic_device_security_chip_card":"shield","ic_tidal_architecture_card":"layers","settings_info_android_ic":"android","settings_info_authentication_ic":"shield","settings_info_camera_ic":"camera","settings_info_contributor_ic":"person","settings_info_cpu_ic":"chip","settings_info_hdd_ic":"storage","settings_info_legal_ic":"document","settings_info_memory_ic":"memory","settings_info_model_ic":"phone","settings_info_sim_ic":"sim","settings_info_state_ic":"info","settings_info_system_ic":"android","settings_info_version_ic":"version","settings_face_password_icon":"face","settings_fingerprint_password_icon":"fingerprint","settings_screen_lock_password_icon":"lock","coui_toolbar_menu_icon_more_disable":"more"}
SYS_IC={"simple_qs_settings_button_drawable_sys":"gear","coui_menu_ic_checkbox_selected_new":"check","notification_guts_settings_icon_final":"gear","vd_autorotate":"rotate","vd_flashlight":"flashlight","vd_theme":"theme","vd_wifi":"wifi","vd_cell":"cell","vd_location":"location","vd_bluetooth":"bluetooth"}
P={
"phone":["M7,2h10c1.1,0 2,0.9 2,2v16c0,1.1 -0.9,2 -2,2H7c-1.1,0 -2,-0.9 -2,-2V4c0,-1.1 0.9,-2 2,-2z","M10,5h4M10,19h4"],
"chip":["M7,7h10v10H7z","M10,10h4v4h-4z","M3,9h3M3,13h3M18,9h3M18,13h3M9,3v3M13,3v3M9,18v3M13,18v3"],
"memory":["M4,6h16v11H4z","M7,9v5M11,9v5M15,9v5","M6,18v2M10,18v2M14,18v2M18,18v2"],
"camera":["M5,7h3l1.5,-2h5L16,7h3c1.1,0 2,0.9 2,2v8c0,1.1 -0.9,2 -2,2H5c-1.1,0 -2,-0.9 -2,-2V9c0,-1.1 0.9,-2 2,-2z","M12,9.5a3.5,3.5 0,1 0,0 7a3.5,3.5 0,1 0,0 -7z"],
"battery":["M4,7h15v10H4z","M20,10v4","M7,10h8v4H7z"],"display":["M3,4h18v13H3z","M9,21h6M12,17v4"],
"shield":["M12,2l8,3v6c0,5 -3.4,9.4 -8,11c-4.6,-1.6 -8,-6 -8,-11V5z","M8.5,12.5l2.2,2.2l4.8,-4.8"],
"layers":["M12,3l9,5l-9,5l-9,-5z","M3,12l9,5l9,-5","M3,16l9,5l9,-5"],
"android":["M7,9h10v8H7z","M9,6l-1.5,-2M15,6l1.5,-2","M5,10v6M19,10v6M9,17v4M15,17v4"],
"person":["M12,4a4,4 0,1 0,0 8a4,4 0,1 0,0 -8z","M4,21c0,-4.4 3.6,-8 8,-8s8,3.6 8,8"],
"storage":["M4,6c0,-2 3.6,-3 8,-3s8,1 8,3s-3.6,3 -8,3s-8,-1 -8,-3z","M4,6v6c0,2 3.6,3 8,3s8,-1 8,-3V6","M4,12v6c0,2 3.6,3 8,3s8,-1 8,-3v-6"],
"document":["M6,2h8l4,4v16H6z","M14,2v5h5","M9,12h6M9,16h6"],"sim":["M7,2h7l5,5v15H7z","M9,11h8v7H9z","M12,11v7M9,14h8"],
"info":["M12,3a9,9 0,1 0,0 18a9,9 0,1 0,0 -18z","M12,10v6"],"version":["M4,4h16v16H4z","M8,9h8M8,13h5M8,17h3"],
"face":["M5,9V5h4M15,5h4v4M5,15v4h4M15,19h4v-4","M9,15c2,2 4,2 6,0"],
"fingerprint":["M7,10c0,-3 2,-5 5,-5s5,2 5,5","M5,10c0,-4 3,-7 7,-7s7,3 7,7","M9,11v2c0,3 -1,5 -2,7","M12,9c2,0 3,1 3,3v2c0,3 1,5 2,6"],
"lock":["M6,10h12v11H6z","M8,10V7a4,4 0,0 1,8 0v3","M12,14v3"],"more":["M6,12h0M12,12h0M18,12h0"],
"gear":["M12,8a4,4 0,1 0,0 8a4,4 0,1 0,0 -8z","M12,2v3M12,19v3M2,12h3M19,12h3M4.9,4.9l2.1,2.1M17,17l2.1,2.1M19.1,4.9L17,7M7,17l-2.1,2.1"],
"check":["M5,12.5l4.2,4.2L19,7"],"rotate":["M19,8V3l-2,2a8,8 0,1 0,2.2,11","M19,3h-5"],
"flashlight":["M8,3h8l-1,5h-6z","M9,8h6l2,5v8H7v-8z"],"theme":["M12,3a9,9 0,1 0,0 18","M8,9h0M12,7h0M16,10h0"],
"wifi":["M3,9c5,-4 13,-4 18,0","M6,13c3.5,-3 8.5,-3 12,0","M9.5,16.5c1.5,-1.2 3.5,-1.2 5,0","M12,20h0"],
"cell":["M5,19v-3h2v3zM9,19v-6h2v6zM13,19v-9h2v9zM17,19V7h2v12z"],
"location":["M12,2a7,7 0,0 0,-7 7c0,5 7,13 7,13s7,-8 7,-13a7,7 0,0 0,-7 -7z","M12,7a2,2 0,1 0,0 4a2,2 0,1 0,0 -4z"],
"bluetooth":["M12,2v20l6,-6l-12,-8l12,-6l-6,-6"]
}
def run(*a):
    c=[str(x) for x in a]; print("+"," ".join(c)); subprocess.run(c,check=True)
def snake(s): return re.sub(r"(?<!^)(?=[A-Z])","_",s).lower()
def sdk():
    root=Path(os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME") or "/usr/local/lib/android/sdk")
    j=root/"platforms"/f"android-{SDK_DIR}"/"android.jar"; b=root/"build-tools"/BT
    q=(j,b/"aapt2",b/"zipalign",b/"apksigner")
    for x in q:
        if not x.is_file(): raise RuntimeError(f"missing {x}")
    return q
def key():
    p=ROOT/"build/signing/debug.keystore"
    if not p.is_file():
        p.parent.mkdir(parents=True,exist_ok=True)
        run("keytool","-genkeypair","-noprompt","-keystore",p,"-storepass","android","-keypass","android","-alias","androiddebugkey","-dname","CN=ColorOS17 Compat,O=ColorOS-Monet,C=US","-keyalg","RSA","-keysize","2048","-validity","10000")
    return p
def ref(role,mode): return f"@android:color/system_{role}_{mode}"
def colors(m3,mat,extra):
    l={}; d={}
    if m3:
        for r in M3:
            l[f"m3_sys_color_dynamic_light_{r}"]=ref(r,"light"); d[f"m3_sys_color_dynamic_light_{r}"]=ref(r,"light")
            l[f"m3_sys_color_dynamic_dark_{r}"]=ref(r,"dark"); d[f"m3_sys_color_dynamic_dark_{r}"]=ref(r,"dark")
        for r in M3FIX: l[f"m3_sys_color_dynamic_{r}"]=ref(r,"light"); d[f"m3_sys_color_dynamic_{r}"]=ref(r,"dark")
    if mat:
        for s in MAT:
            r=snake(s); l["materialColor"+s]=ref(r,"light"); d["materialColor"+s]=ref(r,"dark")
    if extra=="settings":
        fam=["primary","secondary","tertiary"]
        for i,c in enumerate(CATS):
            f=fam[i%3]; l[f"homepage_{c}_background"]=ref(f+"_container","light"); l[f"homepage_{c}_foreground"]=ref("on_"+f+"_container","light")
            d[f"homepage_{c}_background"]=ref(f+"_container","dark"); d[f"homepage_{c}_foreground"]=ref("on_"+f+"_container","dark")
        old={"blue":"primary","cyan":"secondary","green":"tertiary","orange":"primary","pink":"tertiary","purple":"secondary","red":"tertiary","yellow":"secondary","grey":"secondary"}
        for n,f in old.items():
            l[f"homepage_{n}_bg"]=ref(f+"_container","light"); l[f"homepage_{n}_fg"]=ref("on_"+f+"_container","light")
            d[f"homepage_{n}_bg"]=ref(f+"_container","dark"); d[f"homepage_{n}_fg"]=ref("on_"+f+"_container","dark")
        l["homepage_generic_icon_background"]=ref("primary_container","light"); d["homepage_generic_icon_background"]=ref("primary_container","dark")
        l["homepage_category_tile_divider"]=ref("outline_variant","light"); d["homepage_category_tile_divider"]=ref("outline_variant","dark")
    if extra=="permission":
        for n,f in {"blue":"primary","green":"tertiary","red":"tertiary","yellow":"secondary"}.items(): l["privacy_homepage_icon_color_"+n]=ref(f,"light"); d["privacy_homepage_icon_color_"+n]=ref(f,"dark")
    if extra=="contacts": l["coui_navigation_bar_color"]=ref("surface","light"); d["coui_navigation_bar_color"]=ref("surface","dark")
    if extra=="wireless": l["homepage_generic_icon_background"]=ref("primary_container","light"); d["homepage_generic_icon_background"]=ref("primary_container","dark")
    if extra=="systemui": l["notification_setting_menu_row_color"]=ref("surface_container","light"); d["notification_setting_menu_row_color"]=ref("surface_container","dark")
    return l,d
def vxml(k,c):
    ps=P.get(k,P["info"]); body="\n".join(f' <path android:fillColor="@android:color/transparent" android:strokeColor="{c}" android:strokeWidth="1.8" android:strokeLineCap="round" android:strokeLineJoin="round" android:pathData="{p}" />' for p in ps)
    return f'<?xml version="1.0" encoding="utf-8"?>\n<vector xmlns:android="http://schemas.android.com/apk/res/android" android:width="24dp" android:height="24dp" android:viewportWidth="24" android:viewportHeight="24">\n{body}\n</vector>\n'
def icons(extra,night=False):
    c="@android:color/system_primary_dark" if night else "@android:color/system_primary_light"; z={}
    if extra=="settings": z={n:vxml(k,c) for n,k in SET_IC.items()}
    if extra=="launcher": z={"ic_system_shortcut_detail_info":vxml("info",c),"ic_oplus_task_shortcut_app_info":vxml("info",c)}
    if extra=="systemui": z={n:vxml(k,c) for n,k in SYS_IC.items()}
    if extra in ("eyeprotect","phone"): z={"coui_menu_ic_checkbox_selected_new":vxml("check",c)}
    if extra in ("contacts","wireless"):
        cc="@android:color/system_on_surface_dark" if night else "@android:color/system_on_surface_light"; z={"coui_toolbar_menu_icon_more_disable":vxml("more",cc)}
    return z
def write_colors(p,d):
    p.parent.mkdir(parents=True,exist_ok=True); p.write_text('<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'+"\n".join(f' <color name="{k}">{v}</color>' for k,v in sorted(d.items()))+'\n</resources>\n')
def shape(bg,stroke): return f'<?xml version="1.0" encoding="utf-8"?>\n<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle"><solid android:color="{bg}" /><stroke android:width="1dp" android:color="{stroke}" /><corners android:radius="28dp" /></shape>\n'
def project(base,name,cfg,ver,vc):
    pkg,m3,mat,extra=cfg; p=base/name; p.mkdir(parents=True)
    (p/"AndroidManifest.xml").write_text(f'<?xml version="1.0" encoding="utf-8"?>\n<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="dev.zhanfg.coloros17.compat.{name}" android:versionCode="{vc}" android:versionName="{ver}"><uses-sdk android:minSdkVersion="37" android:targetSdkVersion="37" /><application android:allowBackup="false" android:hasCode="false" android:extractNativeLibs="false" /><overlay android:targetPackage="{pkg}" android:isStatic="true" android:priority="900" /></manifest>\n')
    l,d=colors(m3,mat,extra)
    if l: write_colors(p/"res/values/colors.xml",l); write_colors(p/"res/values-night/colors.xml",d)
    for sub,night in [("drawable",False),("drawable-night",True)]:
        for n,x in icons(extra,night).items(): q=p/"res"/sub/(n+".xml"); q.parent.mkdir(parents=True,exist_ok=True); q.write_text(x)
    if extra=="settings":
        for sub,mode in [("drawable","light"),("drawable-night","dark")]:
            for n in ("device_ota_card_bg_17","device_ota_card_bg_17_land"):
                q=p/"res"/sub/(n+".xml"); q.parent.mkdir(parents=True,exist_ok=True); q.write_text(shape(ref("primary_container",mode),ref("outline_variant",mode)))
    return p
def build(p,out,j,a,z,s,k):
    with tempfile.TemporaryDirectory(prefix="cos17-") as td:
        t=Path(td); comp=t/"c.zip"; u=t/"u.apk"; al=t/"a.apk"
        run(a,"compile","--dir",p/"res","-o",comp); run(a,"link","-o",u,"-I",j,"--manifest",p/"AndroidManifest.xml","--auto-add-overlay","--min-sdk-version","37","--target-sdk-version","37",comp)
        run(z,"-f","4",u,al); run(s,"sign","--ks",k,"--ks-pass","pass:android","--ks-key-alias","androiddebugkey","--key-pass","pass:android","--out",out,al); run(s,"verify","--verbose",out)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--version",default="0.1.5"); ap.add_argument("--version-code",type=int,default=26100315); ap.add_argument("--output",type=Path,default=ROOT/"dist/ColorOS17-FullCompat-Overlays.zip"); x=ap.parse_args()
    j,a,z,s=sdk(); k=key(); od=ROOT/"dist/cos17-overlays"; shutil.rmtree(od,ignore_errors=True); od.mkdir(parents=True)
    rows=["key\ttarget_package\toverlay_package\tapk"]
    with tempfile.TemporaryDirectory(prefix="cos17src-") as raw:
        b=Path(raw)
        for i,(n,cfg) in enumerate(TARGETS.items(),1):
            p=project(b,n,cfg,x.version,x.version_code+i); out=od/f"COS17_{n}.apk"; build(p,out,j,a,z,s,k); rows.append(f"{n}\t{cfg[0]}\tdev.zhanfg.coloros17.compat.{n}\t{out.name}")
    (od/"compat-manifest.tsv").write_text("\n".join(rows)+"\n")
    with zipfile.ZipFile(x.output,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as q:
        for p in sorted(od.iterdir()): q.write(p,p.name)
    print("built",len(TARGETS),"overlays ->",x.output)
if __name__=="__main__": raise SystemExit(main())
