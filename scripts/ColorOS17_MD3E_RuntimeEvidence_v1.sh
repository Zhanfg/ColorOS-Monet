#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0
# ColorOS 17 MD3E runtime evidence collector.
# No arguments. Read-only. No reboot, no force-stop, no theme/overlay mutation.

set +e
umask 077

STAMP="$(date +%Y%m%d_%H%M%S 2>/dev/null)"
[ -n "$STAMP" ] || STAMP=unknown

BASE=/sdcard/Download
[ -d "$BASE" ] || BASE=/storage/emulated/0/Download
[ -d "$BASE" ] || BASE="$(pwd)"

WORK="/data/local/tmp/ColorOS17_MD3E_RuntimeEvidence_v1_$STAMP"
OUT="$BASE/ColorOS17_MD3E_RuntimeEvidence_v1_$STAMP.tar.gz"

mkdir -p "$WORK/proc" "$WORK/overlay" "$WORK/runtime" "$WORK/logs" || exit 1

say() { printf '%s\n' "$*"; }
have() { command -v "$1" >/dev/null 2>&1; }

if [ "$(id -u 2>/dev/null)" != 0 ]; then
    say "[!] 需要 root。"
    exit 1
fi

sha_file() {
    file="$1"
    [ -f "$file" ] || return 0
    if have sha256sum; then
        sha256sum "$file" 2>/dev/null
    elif have toybox; then
        toybox sha256sum "$file" 2>/dev/null
    fi
}

pkg_snapshot() {
    pkg="$1"
    safe="$(printf '%s' "$pkg" | tr '.:/' '___')"
    {
        echo "package=$pkg"
        echo "--- pm path ---"
        pm path "$pkg" 2>&1
        echo
        echo "--- version / code path ---"
        dumpsys package "$pkg" 2>/dev/null | grep -E             'versionName=|versionCode=|codePath=|resourcePath=|legacyNativeLibraryDir=|primaryCpuAbi=' | head -n 80
        echo
        echo "--- APK hashes ---"
        pm path "$pkg" 2>/dev/null | sed 's/^package://' | while IFS= read -r p; do
            [ -f "$p" ] && sha_file "$p"
        done
    } > "$WORK/runtime/package_$safe.txt"
}

proc_snapshot() {
    name="$1"
    pid="$(pidof "$name" 2>/dev/null | awk '{print $1}')"
    safe="$(printf '%s' "$name" | tr '.:/' '___')"
    {
        echo "process=$name"
        echo "pid=$pid"
        [ -n "$pid" ] || {
            echo "running=0"
            exit 0
        }
        echo "running=1"
        echo "--- cmdline ---"
        tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null
        echo
        echo "--- status ---"
        cat "/proc/$pid/status" 2>/dev/null | head -n 80
        echo
        echo "--- loaded APK/JAR/framework paths ---"
        awk '{print $6}' "/proc/$pid/maps" 2>/dev/null |             grep -E '^/(system|system_ext|product|my_product|vendor|data/app)/.*\.(apk|jar|so)$' |             sort -u
    } > "$WORK/proc/$safe.txt"
}

say "[1/7] 设备 / ROM / theme ownership"
{
    echo "time=$(date '+%F %T %z' 2>/dev/null)"
    echo "model=$(getprop ro.product.model 2>/dev/null)"
    echo "device=$(getprop ro.product.device 2>/dev/null)"
    echo "sdk=$(getprop ro.build.version.sdk 2>/dev/null)"
    echo "release=$(getprop ro.build.version.release 2>/dev/null)"
    echo "display=$(getprop ro.build.display.id 2>/dev/null)"
    echo "fingerprint=$(getprop ro.build.fingerprint 2>/dev/null)"
    echo "oplusrom=$(getprop ro.build.version.oplusrom 2>/dev/null)"
    echo "selinux=$(getenforce 2>/dev/null)"
    echo
    echo "theme_json=$(settings get secure theme_customization_overlay_packages 2>/dev/null)"
    echo "expressive_prop=$(getprop is_expressive_design_enabled 2>/dev/null)"
    if have device_config; then
        echo "device_config_expressive=$(device_config get android_settings is_expressive_design_enabled 2>/dev/null)"
    fi
    echo "material_blur=$(getprop persist.sys.oplus.material_blur_switch 2>/dev/null)"
    echo "sf_background_blur=$(getprop ro.surface_flinger.supports_background_blur 2>/dev/null)"
    echo "sf_media_panel_blur=$(getprop ro.surface_flinger.media_panel_bg_blur 2>/dev/null)"
    echo "font_scale=$(settings get system font_scale 2>/dev/null)"
    echo "animator_duration_scale=$(settings get global animator_duration_scale 2>/dev/null)"
    echo "transition_animation_scale=$(settings get global transition_animation_scale 2>/dev/null)"
    echo "window_animation_scale=$(settings get global window_animation_scale 2>/dev/null)"
    echo "accessibility_enabled=$(settings get secure accessibility_enabled 2>/dev/null)"
    echo "touch_exploration_enabled=$(settings get secure touch_exploration_enabled 2>/dev/null)"
} > "$WORK/runtime/device_theme.txt"

say "[2/7] 关键包与版本指纹"
for pkg in     com.android.settings     com.android.systemui     com.oplus.systemui.plugins     com.oplus.uxdesign     com.oplus.wirelesssettings     com.oplus.notificationmanager     one.dot.couiexpressive
do
    pkg_snapshot "$pkg"
done

say "[3/7] 当前进程 / classpath provenance"
for proc in     com.android.settings     com.android.systemui     com.oplus.systemui.plugins     com.oplus.uxdesign
do
    proc_snapshot "$proc"
done

say "[4/7] Settings / SystemUI runtime ownership"
{
    echo "--- activities ---"
    dumpsys activity activities 2>/dev/null | grep -E         'mResumedActivity|topResumedActivity|OplusSettingsHomepageActivity|OplusTopLevelSettings|SettingsHomepageActivity|TopLevelSettings|DeviceInfoFragment' | head -n 500
    echo
    echo "--- windows ---"
    dumpsys window windows 2>/dev/null | grep -E         'mCurrentFocus|mFocusedApp|Settings|SystemUI|Volume|Notification|Media|QuickSettings' | head -n 500
} > "$WORK/runtime/activity_window.txt"

{
    echo "--- SurfaceFlinger relevant layers ---"
    dumpsys SurfaceFlinger --list 2>/dev/null | grep -Ei         'status|notification|shade|quick|qs|volume|media|keyguard|lockscreen|settings' | head -n 1000
} > "$WORK/runtime/surface_layers.txt"

say "[5/7] Overlay / idmap / resolved color evidence"
cmd overlay list --user 0 > "$WORK/overlay/overlay_list.txt" 2>&1

for package in     dev.zhanfg.colorosmonet.semantic.settings     dev.zhanfg.colorosmonet.semantic.systemui     dev.zhanfg.colorosmonet.semantic.launcher     dev.zhanfg.colorosmonet.semantic.wirelesssettings     dev.zhanfg.colorosmonet.semantic.notificationmanager
do
    safe="$(printf '%s' "$package" | tr '.:/' '___')"
    cmd overlay dump "$package" > "$WORK/overlay/dump_$safe.txt" 2>&1
done

{
    for spec in         'com.android.settings com.android.settings:color/coui_color_primary_blue'         'com.android.settings com.android.settings:color/coui_color_primary_text_blue'         'com.android.systemui com.android.systemui:color/coui_color_primary_blue'         'com.oplus.wirelesssettings com.oplus.wirelesssettings:color/coui_color_primary_blue'         'com.oplus.notificationmanager com.oplus.notificationmanager:color/coui_color_primary_blue'
    do
        target="$(printf '%s' "$spec" | cut -d' ' -f1)"
        res="$(printf '%s' "$spec" | cut -d' ' -f2)"
        echo "===== $res ====="
        if have timeout; then
            timeout 5 cmd overlay lookup --verbose "$target" "$res" 2>&1
        else
            cmd overlay lookup --verbose "$target" "$res" 2>&1
        fi
        echo
    done
} > "$WORK/overlay/resource_lookup.txt"

find /data/resource-cache -type f 2>/dev/null |     grep -Ei 'colorosmonet|settings|systemui|wireless|notification' |     sort > "$WORK/overlay/idmap_paths.txt"

if have idmap2; then
    while IFS= read -r idmap; do
        [ -f "$idmap" ] || continue
        safe="$(basename "$idmap" | tr '/ :' '___')"
        idmap2 dump --idmap-path "$idmap" > "$WORK/overlay/idmap_$safe.txt" 2>&1
    done < "$WORK/overlay/idmap_paths.txt"
fi

say "[6/7] UXDesign generation fingerprint + relevant exception provenance"
{
    echo "root=/data/oplus/uxres/uxcolor"
    if [ -d /data/oplus/uxres/uxcolor ]; then
        find /data/oplus/uxres/uxcolor -maxdepth 3 -type f 2>/dev/null | sort | while IFS= read -r f; do
            size="$(wc -c < "$f" 2>/dev/null | tr -d ' ')"
            mtime="$(stat -c %Y "$f" 2>/dev/null)"
            sum="$(sha_file "$f" | awk '{print $1}')"
            printf '%s\t%s\t%s\t%s\n' "$f" "$size" "$mtime" "$sum"
        done
    else
        echo "uxcolor_directory_missing=1"
    fi
} > "$WORK/runtime/uxcolor_fingerprint.tsv"

{
    logcat -b all -d -v threadtime 2>/dev/null | grep -Ei         -B 20 -A 60         'NoSuchFieldError|mCardBackgroundColor|COUICustomListSelectedLinearLayout|COUICardListSelectedItemLayout|CardHook|ListHook|MonetColorSpec2025Hook|QsLottieHook|AospMediaCardHook|QSIconViewProxy|SimpleQsClock|OplusVolumeDialogImpl|MediaPlayerCardPageRootView|one\.dot\.couiexpressive' | tail -n 12000
} > "$WORK/logs/targeted_runtime_logcat.txt"

say "[7/7] 摘要与打包"
{
    echo "collector=ColorOS17_MD3E_RuntimeEvidence_v1"
    echo "generated=$(date '+%F %T %z' 2>/dev/null)"
    echo "safety=READ_ONLY"
    echo "reboot=0"
    echo "force_stop=0"
    echo "theme_mutation=0"
    echo "overlay_mutation=0"
    echo "screenshot_capture=0"
    echo "uiautomator_capture=0"
    echo
    echo "Purpose:"
    echo "- identify exact package/process provenance for historical COE failures"
    echo "- fingerprint native UXDesign/theme generation without changing it"
    echo "- record active overlay/idmap/resource resolution"
    echo "- record currently visible Settings/SystemUI ownership signals"
    echo
    echo "Limitations:"
    echo "- this is not Java-object instrumentation"
    echo "- absence of a log line does not prove a component is unused"
    echo "- QS/media/volume active-instance binding may still require a scoped LSPosed trace"
} > "$WORK/README.txt"

find "$WORK" -type f -print0 2>/dev/null | sort -z | xargs -0 sha256sum > "$WORK/SHA256SUMS" 2>/dev/null

tar -czf "$OUT" -C "$WORK" . 2>/dev/null || {
    say "[!] 打包失败，保留：$WORK"
    exit 2
}
sha_file "$OUT" > "$OUT.sha256"
chmod 0644 "$OUT" "$OUT.sha256" 2>/dev/null
rm -rf "$WORK"

say "[✓] 完成：$OUT"
say "[i] 不需要重启；脚本没有修改主题、Overlay、Settings 或 SystemUI。"
