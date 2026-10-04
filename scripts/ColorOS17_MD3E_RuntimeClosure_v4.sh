#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0
# ColorOS 17 MD3E runtime closure v4
# No arguments. No reboot. Restarts Settings only.
# Temporarily toggles is_expressive_design_enabled and restores it on all exits.
# Does NOT mutate theme JSON, OverlayManager, LSPosed scope, SystemUI, or persistent properties.

set +e
umask 077

PROP=is_expressive_design_enabled
STAMP="$(date +%Y%m%d_%H%M%S 2>/dev/null)"
[ -n "$STAMP" ] || STAMP=unknown

OUTROOT=/sdcard/Download
[ -d "$OUTROOT" ] || OUTROOT=/storage/emulated/0/Download
[ -d "$OUTROOT" ] || OUTROOT="$(pwd)"

WORK="/data/local/tmp/ColorOS17_MD3E_RuntimeClosure_v4_$STAMP"
OUT="$OUTROOT/ColorOS17_MD3E_RuntimeClosure_v4_$STAMP.tar.gz"

mkdir -p "$WORK"/{baseline,xml/settings,xml/media,A_off,B_on,restored,runtime,logs} || exit 1

if [ "$(id -u 2>/dev/null)" != 0 ]; then
    echo "[!] 需要 root。"
    exit 1
fi

have(){ command -v "$1" >/dev/null 2>&1; }

RESET_PROP=""
for p in "$(command -v resetprop 2>/dev/null)" /data/adb/ksu/bin/resetprop /data/adb/magisk/resetprop; do
    [ -n "$p" ] && [ -x "$p" ] && { RESET_PROP="$p"; break; }
done
if [ -z "$RESET_PROP" ]; then
    echo "[!] 找不到 resetprop；为保证 property 能完整恢复，停止执行。"
    exit 1
fi

ORIG_VALUE="$(getprop "$PROP" 2>/dev/null)"
getprop 2>/dev/null | grep -Fq "[$PROP]:" && ORIG_PRESENT=1 || ORIG_PRESENT=0

set_prop(){
    "$RESET_PROP" "$PROP" "$1" >/dev/null 2>&1
}

restore_prop(){
    if [ "$ORIG_PRESENT" = 0 ]; then
        "$RESET_PROP" -d "$PROP" >/dev/null 2>&1 || "$RESET_PROP" "$PROP" "" >/dev/null 2>&1
    else
        "$RESET_PROP" "$PROP" "$ORIG_VALUE" >/dev/null 2>&1
    fi
}

restart_settings(){
    am force-stop com.android.settings >/dev/null 2>&1
    sleep 1
}

cleanup(){
    restore_prop
    restart_settings
}
trap cleanup 1 2 15

apk_path(){
    pm path "$1" 2>/dev/null | sed -n 's/^package://p' | head -n 1
}

hash_file(){
    [ -f "$1" ] && sha256sum "$1" 2>/dev/null
}

sanitize_xml(){
    src="$1"
    dst="$2"
    [ -f "$src" ] || return 0
    sed -E         's/text="[^"]*"/text=""/g;
         s/content-desc="[^"]*"/content-desc=""/g;
         s/hint="[^"]*"/hint=""/g'         "$src" > "$dst" 2>/dev/null
    rm -f "$src"
}

extract_zip_entry(){
    apk="$1"
    entry="$2"
    root="$3"
    [ -f "$apk" ] || return 0
    unzip -Z1 "$apk" 2>/dev/null | grep -Fxq "$entry" || return 0
    mkdir -p "$root/$(dirname "$entry")"
    unzip -p "$apk" "$entry" > "$root/$entry" 2>/dev/null
}

capture_screen(){
    root="$1"
    name="$2"
    action="$3"
    dir="$root/$name"
    mkdir -p "$dir"

    {
        echo "name=$name"
        echo "action=$action"
        echo "property=$(getprop "$PROP" 2>/dev/null)"
        echo "--- am start ---"
        am start -W -a "$action" -p com.android.settings 2>&1
        echo "--- activity ---"
        dumpsys activity activities 2>/dev/null |             grep -E 'mResumedActivity|topResumedActivity|OplusSettingsHomepageActivity|OplusTopLevelSettings|DeviceInfoFragment|Settings\$' |             head -n 180
        echo "--- window ---"
        dumpsys window windows 2>/dev/null |             grep -E 'mCurrentFocus|mFocusedApp' | head -n 80
    } > "$dir/state.txt"

    sleep 2
    screencap -p "$dir/screen.png" >/dev/null 2>&1

    if have uiautomator; then
        uiautomator dump "$dir/raw.xml" >/dev/null 2>&1
        sanitize_xml "$dir/raw.xml" "$dir/window.xml"
    fi
}

capture_set(){
    root="$1"
    capture_screen "$root" "00_home"     "android.settings.SETTINGS"
    capture_screen "$root" "01_display"  "android.settings.DISPLAY_SETTINGS"
    capture_screen "$root" "02_sound"    "android.settings.SOUND_SETTINGS"
    capture_screen "$root" "03_security" "android.settings.SECURITY_SETTINGS"
    capture_screen "$root" "04_privacy"  "android.settings.PRIVACY_SETTINGS"
    capture_screen "$root" "05_about"    "android.settings.DEVICE_INFO_SETTINGS"
}

compare_pair(){
    name="$1"
    a="$WORK/A_off/$name"
    b="$WORK/B_on/$name"

    echo "[$name]"
    if [ -f "$a/screen.png" ] && [ -f "$b/screen.png" ]; then
        ah="$(sha256sum "$a/screen.png" 2>/dev/null | awk '{print $1}')"
        bh="$(sha256sum "$b/screen.png" 2>/dev/null | awk '{print $1}')"
        echo "screen_a=$ah"
        echo "screen_b=$bh"
        [ -n "$ah" ] && [ "$ah" = "$bh" ] && echo "screen_changed=0" || echo "screen_changed=1"
    else
        echo "screen_missing=1"
    fi

    if [ -f "$a/window.xml" ] && [ -f "$b/window.xml" ]; then
        cmp -s "$a/window.xml" "$b/window.xml"
        [ $? -eq 0 ] && echo "uia_changed=0" || echo "uia_changed=1"
        echo "uia_a_nodes=$(grep -o '<node ' "$a/window.xml" 2>/dev/null | wc -l | tr -d ' ')"
        echo "uia_b_nodes=$(grep -o '<node ' "$b/window.xml" 2>/dev/null | wc -l | tr -d ' ')"
    else
        echo "uia_missing=1"
    fi
    echo
}

echo "[1/7] 记录设备、主题与目标包基线"

SETTINGS_APK="$(apk_path com.android.settings)"
SYSTEMUI_APK="$(apk_path com.android.systemui)"
PLUGIN_APK="$(apk_path com.oplus.systemui.plugins)"
UXDESIGN_APK="$(apk_path com.oplus.uxdesign)"
COE_APK="$(apk_path one.dot.couiexpressive)"

{
    echo "collector=ColorOS17_MD3E_RuntimeClosure_v4"
    echo "time=$(date '+%F %T %z' 2>/dev/null)"
    echo "model=$(getprop ro.product.model 2>/dev/null)"
    echo "device=$(getprop ro.product.device 2>/dev/null)"
    echo "sdk=$(getprop ro.build.version.sdk 2>/dev/null)"
    echo "release=$(getprop ro.build.version.release 2>/dev/null)"
    echo "display=$(getprop ro.build.display.id 2>/dev/null)"
    echo "fingerprint=$(getprop ro.build.fingerprint 2>/dev/null)"
    echo "oplusrom=$(getprop ro.build.version.oplusrom 2>/dev/null)"
    echo "property=$PROP"
    echo "original_present=$ORIG_PRESENT"
    echo "original_value=$ORIG_VALUE"
    echo "resetprop=$RESET_PROP"
    echo "theme_json=$(settings get secure theme_customization_overlay_packages 2>/dev/null)"
    echo "material_blur=$(getprop persist.sys.oplus.material_blur_switch 2>/dev/null)"
    echo "sf_background_blur=$(getprop ro.surface_flinger.supports_background_blur 2>/dev/null)"
    echo "settings_apk=$SETTINGS_APK"
    echo "systemui_apk=$SYSTEMUI_APK"
    echo "plugin_apk=$PLUGIN_APK"
    echo "uxdesign_apk=$UXDESIGN_APK"
    echo "coe_apk=$COE_APK"
} > "$WORK/baseline/device.txt"

for f in "$SETTINGS_APK" "$SYSTEMUI_APK" "$PLUGIN_APK" "$UXDESIGN_APK" "$COE_APK"; do
    hash_file "$f"
done > "$WORK/baseline/apk_sha256.txt"

pm path com.android.settings > "$WORK/baseline/settings_paths.txt" 2>&1
pm path com.android.systemui > "$WORK/baseline/systemui_paths.txt" 2>&1
pm path com.oplus.systemui.plugins > "$WORK/baseline/systemuiplugin_paths.txt" 2>&1
pm path com.oplus.uxdesign > "$WORK/baseline/uxdesign_paths.txt" 2>&1
pm path one.dot.couiexpressive > "$WORK/baseline/coe_paths.txt" 2>&1

echo "[2/7] 提取 Settings / SystemUIPlugin 的关键结构 XML"

for e in     res/xml/top_level_settings_oplus.xml     res/xml/top_level_settings.xml     res/xml/top_level_settings_expressive.xml     res/xml/top_level_settings_expressive_desktop.xml     res/layout/settingslib_expressive_preference_card.xml     res/layout-v36/settingslib_expressive_preference.xml     res/layout-v36/settingslib_expressive_preference_switch.xml     res/drawable/card_list_item_head_bg.xml     res/drawable/card_list_item_body_bg.xml     res/drawable/card_list_item_foot_bg.xml     res/drawable/card_list_item_full_bg.xml     res/drawable/settingslib_expressive_card_background.xml
do
    extract_zip_entry "$SETTINGS_APK" "$e" "$WORK/xml/settings"
done

if [ -f "$PLUGIN_APK" ]; then
    for e in         res/Jc.xml res/OG.xml res/di.xml res/jK.xml res/wN.xml res/Dy.xml         res/8o.xml res/lV.xml res/Ww.xml res/Mq.xml res/9_.xml res/60.xml
    do
        extract_zip_entry "$PLUGIN_APK" "$e" "$WORK/xml/media"
    done
    unzip -p "$PLUGIN_APK" resources.arsc > "$WORK/xml/media/resources.arsc" 2>/dev/null
    unzip -p "$PLUGIN_APK" AndroidManifest.xml > "$WORK/xml/media/AndroidManifest.xml" 2>/dev/null
fi

echo "[3/7] A：关闭 native Expressive gate，采集六个 Settings 场景"
set_prop false
restart_settings
capture_set "$WORK/A_off"

echo "[4/7] B：开启 native Expressive gate，采集六个 Settings 场景"
set_prop true
restart_settings
capture_set "$WORK/B_on"

echo "[5/7] 恢复原始 property 并验证"
restore_prop
restart_settings
capture_screen "$WORK/restored" "00_home" "android.settings.SETTINGS"

{
    echo "property_after_restore=$(getprop "$PROP" 2>/dev/null)"
    echo "original_present=$ORIG_PRESENT"
    echo "original_value=$ORIG_VALUE"
    echo
    for name in 00_home 01_display 02_sound 03_security 04_privacy 05_about; do
        compare_pair "$name"
    done
} > "$WORK/runtime/ab_summary.txt"

echo "[6/7] 收集剩余 SystemUI / COE 运行时证据"

cmd overlay list --user 0 > "$WORK/runtime/overlay_list.txt" 2>&1

{
    echo "--- activity/window ---"
    dumpsys window windows 2>/dev/null |         grep -E 'mCurrentFocus|mFocusedApp|Settings|SystemUI|Volume|Media|QuickSettings' |         head -n 600
    echo
    echo "--- SurfaceFlinger layers ---"
    dumpsys SurfaceFlinger --list 2>/dev/null |         grep -Ei 'notification|shade|quick|qs|volume|media|keyguard|settings' |         head -n 1200
    echo
    echo "--- media sessions ---"
    dumpsys media_session 2>/dev/null | head -n 1200
} > "$WORK/runtime/components.txt"

logcat -b all -d -v threadtime 2>/dev/null |     grep -Ei -B20 -A60     'NoSuchFieldError|mCardBackgroundColor|CardHook|ListHook|QSIconViewProxy|SimpleQsClock|OplusVolumeDialogImpl|VolumeMaterialCapability|MediaPlayerCardPageRootView|MonetColorSpec2025Hook|QsLottieHook|AospMediaCardHook|one\.dot\.couiexpressive|Resources\$NotFoundException|FATAL EXCEPTION' |     tail -n 16000 > "$WORK/logs/targeted.txt"

echo "[7/7] 生成摘要并打包"

{
    echo "collector=ColorOS17_MD3E_RuntimeClosure_v4"
    echo "reboot=0"
    echo "settings_restart=1"
    echo "systemui_restart=0"
    echo "theme_json_mutation=0"
    echo "overlay_mutation=0"
    echo "lsposed_scope_mutation=0"
    echo "persistent_property_mutation=0"
    echo "temporary_property=$PROP"
    echo "original_property_present=$ORIG_PRESENT"
    echo "original_property_value=$ORIG_VALUE"
    echo "restored_property_value=$(getprop "$PROP" 2>/dev/null)"
    echo "settings_screens=A_off+B_on+restored_home"
    echo "uia_text_sanitized=1"
    echo
    echo "Interpretation:"
    echo "- screen_changed=1 proves pixels changed, not that the result is correct."
    echo "- uia_changed=1 proves hierarchy/bounds changed."
    echo "- OPlus homepage icon/tint ownership must remain intact."
    echo "- About Device remains component-specific; no generic card transform is expected."
    echo "- SystemUI evidence is observational only; SystemUI is never restarted."
} > "$WORK/README.txt"

find "$WORK" -type f -print0 2>/dev/null | sort -z | xargs -0 sha256sum > "$WORK/SHA256SUMS" 2>/dev/null

tar -czf "$OUT" -C "$WORK" . 2>/dev/null || {
    echo "[!] 打包失败，原始目录保留：$WORK"
    cleanup
    exit 2
}

sha256sum "$OUT" > "$OUT.sha256" 2>/dev/null
chmod 0644 "$OUT" "$OUT.sha256" 2>/dev/null

restore_prop
trap - 1 2 15
restart_settings
am start -W -a android.settings.SETTINGS -p com.android.settings >/dev/null 2>&1

SIZE="$(wc -c < "$OUT" 2>/dev/null | tr -d ' ')"
case "$SIZE" in ''|*[!0-9]*) SIZE=0 ;; esac

if [ "$SIZE" -gt 8388608 ]; then
    PARTDIR="$OUT.parts"
    rm -rf "$PARTDIR"
    mkdir -p "$PARTDIR"
    split -b 8m -d -a 3 "$OUT" "$PARTDIR/$(basename "$OUT").part-" 2>/dev/null
    {
        echo "source=$(basename "$OUT")"
        echo "source_size=$SIZE"
        echo "source_sha256=$(sha256sum "$OUT" 2>/dev/null | awk '{print $1}')"
        echo "reassemble=cat $(basename "$OUT").part-* > $(basename "$OUT")"
        for f in "$PARTDIR"/*.part-*; do
            [ -f "$f" ] && sha256sum "$f"
        done
    } > "$PARTDIR/SPLIT_MANIFEST.txt"
    chmod 0644 "$PARTDIR"/* 2>/dev/null
    echo "[✓] 分卷目录：$PARTDIR"
fi

echo "[✓] $OUT"
echo "[✓] property restored: '$(getprop "$PROP" 2>/dev/null)'"
rm -rf "$WORK"
