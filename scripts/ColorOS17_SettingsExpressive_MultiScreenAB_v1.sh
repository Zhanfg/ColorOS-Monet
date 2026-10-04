#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0
# ColorOS 17 Settings native-Expressive multi-screen A/B collector v1
# No arguments. No reboot. Temporarily restarts Settings only.
# Restores the original is_expressive_design_enabled property before exit.

set +e
umask 077

PROP=is_expressive_design_enabled
STAMP="$(date +%Y%m%d_%H%M%S 2>/dev/null)"
[ -n "$STAMP" ] || STAMP=unknown
OUTROOT=/sdcard/Download
[ -d "$OUTROOT" ] || OUTROOT=/storage/emulated/0/Download
[ -d "$OUTROOT" ] || OUTROOT="$(pwd)"

WORK="/data/local/tmp/ColorOS17_SettingsExpressive_MultiScreenAB_v1_$STAMP"
OUT="$OUTROOT/ColorOS17_SettingsExpressive_MultiScreenAB_v1_$STAMP.tar.gz"
mkdir -p "$WORK"/{baseline,A_off,B_on,restored} || exit 1

[ "$(id -u 2>/dev/null)" = 0 ] || {
    echo "[!] 需要 root。"
    exit 1
}

have(){ command -v "$1" >/dev/null 2>&1; }

RESET_PROP=""
for p in "$(command -v resetprop 2>/dev/null)" /data/adb/ksu/bin/resetprop /data/adb/magisk/resetprop; do
    [ -n "$p" ] && [ -x "$p" ] && { RESET_PROP="$p"; break; }
done
if [ -z "$RESET_PROP" ]; then
    echo "[!] 没有找到 resetprop。为了能完整恢复 property，不继续执行。"
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

sanitize_xml(){
    src="$1"
    dst="$2"
    [ -f "$src" ] || return 0
    sed -E         's/text="[^"]*"/text=""/g;
         s/content-desc="[^"]*"/content-desc=""/g;
         s/hint="[^"]*"/hint=""/g'         "$src" > "$dst" 2>/dev/null
    rm -f "$src"
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
        echo "--- start ---"
        am start -W -a "$action" -p com.android.settings 2>&1
        echo "--- focus ---"
        dumpsys activity activities 2>/dev/null |             grep -E 'mResumedActivity|topResumedActivity|OplusSettingsHomepageActivity|OplusTopLevelSettings|DeviceInfoFragment' |             head -n 120
        dumpsys window windows 2>/dev/null |             grep -E 'mCurrentFocus|mFocusedApp' | head -n 50
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
    else
        echo "uia_missing=1"
    fi
    echo
}

cleanup(){
    restore_prop
    restart_settings
}
trap cleanup 1 2 15

{
    echo "collector=ColorOS17_SettingsExpressive_MultiScreenAB_v1"
    echo "time=$(date '+%F %T %z' 2>/dev/null)"
    echo "model=$(getprop ro.product.model 2>/dev/null)"
    echo "device=$(getprop ro.product.device 2>/dev/null)"
    echo "sdk=$(getprop ro.build.version.sdk 2>/dev/null)"
    echo "display=$(getprop ro.build.display.id 2>/dev/null)"
    echo "fingerprint=$(getprop ro.build.fingerprint 2>/dev/null)"
    echo "property=$PROP"
    echo "original_present=$ORIG_PRESENT"
    echo "original_value=$ORIG_VALUE"
    echo "resetprop=$RESET_PROP"
    echo "theme_json=$(settings get secure theme_customization_overlay_packages 2>/dev/null)"
} > "$WORK/baseline/device.txt"

pm path com.android.settings > "$WORK/baseline/settings_paths.txt" 2>&1
SETTINGS_APK="$(sed -n 's/^package://p' "$WORK/baseline/settings_paths.txt" | head -n 1)"
[ -f "$SETTINGS_APK" ] && sha256sum "$SETTINGS_APK" > "$WORK/baseline/settings_sha256.txt" 2>/dev/null

echo "[1/4] A：关闭 native Expressive gate"
set_prop false
restart_settings
capture_set "$WORK/A_off"

echo "[2/4] B：开启 native Expressive gate"
set_prop true
restart_settings
capture_set "$WORK/B_on"

echo "[3/4] 恢复原始 property"
restore_prop
restart_settings
capture_screen "$WORK/restored" "00_home" "android.settings.SETTINGS"

echo "[4/4] 生成差异摘要"
{
    echo "property_after_restore=$(getprop "$PROP" 2>/dev/null)"
    echo "original_present=$ORIG_PRESENT"
    echo "original_value=$ORIG_VALUE"
    echo
    for name in 00_home 01_display 02_sound 03_security 04_privacy 05_about; do
        compare_pair "$name"
    done
    echo "interpretation:"
    echo "- screen_changed=1 only proves rendered pixels changed; inspect screenshots."
    echo "- uia_changed=1 indicates hierarchy/bounds changed, not necessarily correctness."
    echo "- this probe does not alter Monet/theme JSON or overlays."
    echo "- Settings is the only process intentionally force-stopped."
} > "$WORK/AB_SUMMARY.txt"

{
    echo "READ_ONLY_THEME_JSON=1"
    echo "NO_REBOOT=1"
    echo "NO_OVERLAY_MUTATION=1"
    echo "TEMP_PROPERTY_MUTATION=1"
    echo "PROPERTY_RESTORED=1"
    echo "SETTINGS_RESTARTED=1"
    echo "SYSTEMUI_RESTARTED=0"
    echo "UI_TEXT_SANITIZED=1"
} > "$WORK/README.txt"

find "$WORK" -type f -print0 2>/dev/null | sort -z | xargs -0 sha256sum > "$WORK/SHA256SUMS" 2>/dev/null

tar -czf "$OUT" -C "$WORK" . 2>/dev/null || {
    echo "[!] 打包失败，保留目录：$WORK"
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
