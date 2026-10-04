#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0
# One-shot read-only runtime evidence collector for ColorOS 17 MD3E integration.
# No arguments. No reboot. No package/overlay/theme mutation.

set +e
umask 077

STAMP="$(date +%Y%m%d_%H%M%S 2>/dev/null)"
[ -n "$STAMP" ] || STAMP=unknown

OUTROOT="/sdcard/Download"
[ -d "$OUTROOT" ] || OUTROOT="/storage/emulated/0/Download"
[ -d "$OUTROOT" ] || OUTROOT="$(pwd)"

WORK="/data/local/tmp/ColorOS17_MD3E_RuntimeEvidence_v1_$STAMP"
META="$WORK/meta"
UX="$WORK/uxcolor"
IDMAP="$WORK/idmap"
OUT="$OUTROOT/ColorOS17_MD3E_RuntimeEvidence_v1_$STAMP.tar.gz"

mkdir -p "$META" "$UX" "$IDMAP" || exit 1

say() { printf '%s\n' "$*"; }
have() { command -v "$1" >/dev/null 2>&1; }

if [ "$(id -u 2>/dev/null)" != 0 ]; then
    say "[!] 需要 root 执行。"
    exit 1
fi

capture() {
    file="$1"
    shift
    {
        printf '$'
        for a in "$@"; do printf ' %s' "$a"; done
        printf '\n'
        "$@"
        rc=$?
        printf '\nexit_code=%s\n' "$rc"
    } > "$file" 2>&1
}

pkg_dump() {
    pkg="$1"
    safe="$(printf '%s' "$pkg" | tr '.:/' '___')"
    {
        echo "package=$pkg"
        echo "--- pm path ---"
        pm path "$pkg" 2>&1
        echo
        echo "--- dumpsys package summary ---"
        dumpsys package "$pkg" 2>/dev/null | grep -E             'versionName=|versionCode=|codePath=|resourcePath=|legacyNativeLibraryDir=|primaryCpuAbi=|targetSdk=' | head -n 80
        echo
        echo "--- APK hashes ---"
        pm path "$pkg" 2>/dev/null | sed 's/^package://' | while IFS= read -r p; do
            [ -f "$p" ] || continue
            sha256sum "$p" 2>/dev/null || true
        done
    } > "$META/pkg_$safe.txt"
}

say "[1/8] Device / build / display baseline"
{
    echo "time=$(date '+%F %T %z' 2>/dev/null)"
    echo "uid=$(id -u 2>/dev/null)"
    echo "model=$(getprop ro.product.model 2>/dev/null)"
    echo "device=$(getprop ro.product.device 2>/dev/null)"
    echo "sdk=$(getprop ro.build.version.sdk 2>/dev/null)"
    echo "release=$(getprop ro.build.version.release 2>/dev/null)"
    echo "display=$(getprop ro.build.display.id 2>/dev/null)"
    echo "fingerprint=$(getprop ro.build.fingerprint 2>/dev/null)"
    echo "oplusrom=$(getprop ro.build.version.oplusrom 2>/dev/null)"
    echo "selinux=$(getenforce 2>/dev/null)"
    echo
    wm size 2>&1
    wm density 2>&1
    echo "font_scale=$(settings get system font_scale 2>/dev/null)"
    echo "material_blur=$(getprop persist.sys.oplus.material_blur_switch 2>/dev/null)"
    echo "sf_background_blur=$(getprop ro.surface_flinger.supports_background_blur 2>/dev/null)"
    echo "sf_media_panel_blur=$(getprop ro.surface_flinger.media_panel_bg_blur 2>/dev/null)"
} > "$META/device.txt"

say "[2/8] Package provenance / hashes"
for pkg in     com.android.settings     com.android.systemui     com.oplus.systemui.plugins     com.oplus.uxdesign     one.dot.couiexpressive     com.oplus.wirelesssettings     com.oplus.notificationmanager     com.android.launcher
do
    pkg_dump "$pkg"
done

say "[3/8] Theme / UXDesign runtime state"
{
    echo "theme_customization_overlay_packages=$(settings get secure theme_customization_overlay_packages 2>/dev/null)"
    echo "oos_theme_customization_two_tone=$(settings get secure oos_theme_customization_two_tone 2>/dev/null)"
    echo
    echo "--- secure theme/color keys ---"
    settings list secure 2>/dev/null | grep -Ei 'theme|monet|material|color|wallpaper|expressive' | head -n 600
    echo
    echo "--- system theme/color keys ---"
    settings list system 2>/dev/null | grep -Ei 'theme|monet|material|color|wallpaper|expressive' | head -n 600
    echo
    echo "--- global theme/color keys ---"
    settings list global 2>/dev/null | grep -Ei 'theme|monet|material|color|wallpaper|expressive' | head -n 600
} > "$META/theme_state.txt"

if [ -d /data/oplus/uxres/uxcolor ]; then
    find /data/oplus/uxres/uxcolor -maxdepth 4 -type f 2>/dev/null | sort > "$UX/file_list.txt"

    find /data/oplus/uxres/uxcolor -maxdepth 4 -type f 2>/dev/null | while IFS= read -r f; do
        [ -f "$f" ] || continue
        size="$(wc -c < "$f" 2>/dev/null | tr -d ' ')"
        case "$size" in ''|*[!0-9]*) continue ;; esac
        [ "$size" -le 262144 ] || continue
        case "$f" in
            *.xml|*.json|*.txt)
                rel="$(printf '%s' "$f" | sed 's#^/data/oplus/uxres/uxcolor/##')"
                dst="$UX/files/$rel"
                mkdir -p "$(dirname "$dst")"
                cp -f "$f" "$dst" 2>/dev/null
                ;;
        esac
    done

    find /data/oplus/uxres/uxcolor -maxdepth 4 -type f 2>/dev/null | while IFS= read -r f; do
        sha256sum "$f" 2>/dev/null
    done > "$UX/sha256.txt"
fi

say "[4/8] Activity / window ownership snapshot"
{
    echo "--- resumed activities ---"
    dumpsys activity activities 2>/dev/null | grep -E         'mResumedActivity|topResumedActivity|ResumedActivity|mFocusedApp' | head -n 200
    echo
    echo "--- focused windows ---"
    dumpsys window windows 2>/dev/null | grep -E         'mCurrentFocus|mFocusedApp|Window #|mAttrs|package=' | head -n 800
} > "$META/activity_window.txt"

say "[5/8] OverlayManager / idmap state"
capture "$META/overlay_list.txt" cmd overlay list --user 0
{
    cmd overlay list --user 0 2>/dev/null | grep -Ei         'settings|systemui|launcher|wireless|notification|zhanfg|monet|expressive' || true
} > "$META/overlay_relevant.txt"

if have idmap2; then
    find /data/resource-cache -type f -name '*@idmap' 2>/dev/null | while IFS= read -r f; do
        base="$(basename "$f")"
        low="$(printf '%s' "$base" | tr '[:upper:]' '[:lower:]')"
        case "$low" in
            *settings*|*systemui*|*launcher*|*wireless*|*notification*|*monet*|*expressive*)
                idmap2 dump --idmap-path "$f" > "$IDMAP/$base.txt" 2>&1
                ;;
        esac
    done
fi

say "[6/8] Effective resource lookups"
{
    for spec in         'com.android.settings com.android.settings:color/coui_color_primary_blue'         'com.android.settings com.android.settings:dimen/coui_list_divider_height'         'com.android.settings com.android.settings:color/coui_color_divider'         'com.android.settings com.android.settings:color/coui_color_card_background'         'com.android.systemui com.android.systemui:color/coui_color_primary_blue'         'com.android.systemui com.android.systemui:dimen/notification_corner_radius'         'com.android.systemui com.android.systemui:color/qs_hl_tile_indicator_active_bg_color'         'com.android.launcher com.android.launcher:dimen/coui_round_corner_s'         'com.oplus.wirelesssettings com.oplus.wirelesssettings:color/coui_color_primary_blue'
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
} > "$META/resource_lookup.txt"

say "[7/8] COE / Settings / SystemUI failure evidence"
{
    logcat -b all -d -v threadtime 2>/dev/null | grep -Ei         'one\.dot\.couiexpressive|CardHook|ListHook|MonetColorSpec2025Hook|QsLottieHook|AospMediaCardHook|mCardBackgroundColor|NoSuchFieldError|COUICardListSelectedItemLayout|COUICustomListSelectedLinearLayout|QSIconViewProxy|OplusVolumeDialogImpl|MediaPlayerCardPageRootView|FATAL EXCEPTION' | tail -n 12000
} > "$META/logcat_relevant.txt"

{
    echo "--- framework / OPlus provenance ---"
    ls -l         /system/framework/framework.jar         /system/framework/framework-res.apk         /system_ext/framework/oplus-framework.jar         /system_ext/framework/oplus-framework-res.apk         /system_ext/framework/oplus-services.jar         2>&1
    echo
    sha256sum         /system/framework/framework.jar         /system/framework/framework-res.apk         /system_ext/framework/oplus-framework.jar         /system_ext/framework/oplus-framework-res.apk         /system_ext/framework/oplus-services.jar         2>/dev/null
} > "$META/framework_provenance.txt"

say "[8/8] Manifest / archive"
{
    echo "collector=ColorOS17_MD3E_RuntimeEvidence_v1"
    echo "policy=READ_ONLY"
    echo "no_reboot=1"
    echo "no_force_stop=1"
    echo "no_overlay_mutation=1"
    echo "no_theme_mutation=1"
    echo "no_private_app_data=1"
    echo "purpose=Codex post-analysis runtime evidence"
    echo
    echo "Known remaining gates:"
    echo "- actual COE NoSuchFieldError class/loader provenance"
    echo "- Settings exact screen/component tuple + XML consumer"
    echo "- SystemUI QS/notification/media/volume/clock active instance"
    echo "- UXDesign user-theme ownership behavior"
} > "$META/README.txt"

tar -czf "$OUT" -C "$WORK" . 2>/dev/null
RC=$?

if [ "$RC" -eq 0 ] && [ -f "$OUT" ]; then
    sha256sum "$OUT" > "$OUT.sha256" 2>/dev/null
    chmod 0644 "$OUT" "$OUT.sha256" 2>/dev/null
    say "[✓] $OUT"
    rm -rf "$WORK"
    exit 0
fi

say "[!] 打包失败，保留目录：$WORK"
exit 2
