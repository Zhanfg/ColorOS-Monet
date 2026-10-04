#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0
# ColorOS 17 × MD3E runtime evidence collector.
# No arguments. Read-only: does not change theme, overlays, package state or restart services/apps.

set +e
umask 077

STAMP="$(date +%Y%m%d_%H%M%S 2>/dev/null)"
[ -n "$STAMP" ] || STAMP=unknown
BASE=/sdcard/Download
[ -d "$BASE" ] || BASE=/storage/emulated/0/Download
WORK="/data/local/tmp/ColorOS17_MD3E_RuntimeEvidence_v1_$STAMP"
OUT="$BASE/ColorOS17_MD3E_RuntimeEvidence_v1_$STAMP.tar.gz"

mkdir -p "$WORK/meta" "$WORK/theme" "$WORK/overlay" "$WORK/packages" "$WORK/logs" "$WORK/ui" "$WORK/hashes" || exit 1

say() { printf '%s\n' "$*"; }
have() { command -v "$1" >/dev/null 2>&1; }

if [ "$(id -u 2>/dev/null)" != "0" ]; then
    say "[!] 需要 root 执行。"
    exit 1
fi

say "============================================================"
say " ColorOS 17 × MD3E Runtime Evidence v1"
say " READ ONLY / NO RESTART / NO THEME OR OVERLAY MUTATION"
say "============================================================"

say "[1/8] Device / build / process baseline"
{
    echo "time=$(date '+%F %T %z' 2>/dev/null)"
    echo "model=$(getprop ro.product.model 2>/dev/null)"
    echo "device=$(getprop ro.product.device 2>/dev/null)"
    echo "sdk=$(getprop ro.build.version.sdk 2>/dev/null)"
    echo "release=$(getprop ro.build.version.release 2>/dev/null)"
    echo "display=$(getprop ro.build.display.id 2>/dev/null)"
    echo "oplusrom=$(getprop ro.build.version.oplusrom 2>/dev/null)"
    echo "fingerprint=$(getprop ro.build.fingerprint 2>/dev/null)"
    echo "kernel=$(uname -a 2>/dev/null)"
    echo "selinux=$(getenforce 2>/dev/null)"
    echo "density=$(wm density 2>&1 | tr '\n' ';')"
    echo "size=$(wm size 2>&1 | tr '\n' ';')"
    echo
    echo "--- relevant processes ---"
    ps -A 2>/dev/null | grep -Ei 'systemui|settings|launcher|uxdesign|couiexpressive|lspd|zygote' || true
} > "$WORK/meta/device.txt"

say "[2/8] UXDesign / native Monet ownership evidence"
{
    echo "--- theme_customization_overlay_packages ---"
    settings get secure theme_customization_overlay_packages 2>&1
    echo
    echo "--- relevant settings ---"
    settings list secure 2>/dev/null | grep -Ei 'theme|monet|material|wallpaper|color|expressive' || true
    settings list system 2>/dev/null | grep -Ei 'theme|monet|material|wallpaper|color|expressive' || true
    settings list global 2>/dev/null | grep -Ei 'theme|monet|material|wallpaper|color|expressive' || true
    echo
    echo "--- blur/system properties ---"
    getprop 2>/dev/null | grep -Ei 'material.*blur|background.*blur|media.*blur|theme|monet|uxcolor|coloros|oplusrom' || true
} > "$WORK/theme/runtime.txt"

for d in /data/oplus/uxres/uxcolor /data/oplus/uxres/uxcolor/temp; do
    [ -d "$d" ] || continue
    {
        echo "directory=$d"
        find "$d" -maxdepth 2 -type f 2>/dev/null | sort
    } >> "$WORK/theme/uxcolor-files.txt"
    find "$d" -maxdepth 2 -type f \( -name '*.xml' -o -name '*.txt' \) 2>/dev/null | while IFS= read -r f; do
        safe="$(printf '%s' "$f" | sed 's#^/##;s#[/ :]#_#g')"
        cp -f "$f" "$WORK/theme/$safe" 2>/dev/null
        {
            printf '%s\t' "$f"
            stat -c '%s\t%Y' "$f" 2>/dev/null || true
            if have sha256sum; then sha256sum "$f" 2>/dev/null | awk '{print $1}'; else echo; fi
        } >> "$WORK/theme/uxcolor-file-state.tsv"
    done
done

say "[3/8] Package provenance and hashes"
PKGS="
com.android.settings
com.android.systemui
com.android.launcher
com.oplus.uxdesign
com.oplus.systemui.plugins
one.dot.couiexpressive
com.oplus.wirelesssettings
com.oplus.notificationmanager
"
for pkg in $PKGS; do
    {
        echo "===== $pkg ====="
        pm path "$pkg" 2>&1
        dumpsys package "$pkg" 2>/dev/null | grep -E 'versionCode=|versionName=|codePath=|resourcePath=|legacyNativeLibraryDir=|primaryCpuAbi=' | head -n 40
    } > "$WORK/packages/$pkg.txt"

    pm path "$pkg" 2>/dev/null | sed 's/^package://' | while IFS= read -r p; do
        [ -f "$p" ] || continue
        if have sha256sum; then
            sha256sum "$p" >> "$WORK/hashes/package-apks.sha256"
        fi
    done
done

say "[4/8] OverlayManager / idmap state"
cmd overlay list --user 0 > "$WORK/overlay/list.txt" 2>&1
for pkg in com.android.settings com.android.systemui com.android.launcher com.oplus.wirelesssettings com.oplus.notificationmanager; do
    cmd overlay list --user 0 2>/dev/null | grep -F "$pkg" > "$WORK/overlay/$pkg.txt" 2>/dev/null || true
done

if have idmap2; then
    find /data/resource-cache -type f -name '*@idmap' 2>/dev/null | while IFS= read -r f; do
        name="$(basename "$f")"
        low="$(printf '%s' "$name" | tr '[:upper:]' '[:lower:]')"
        case "$low" in
            *settings*|*systemui*|*launcher*|*ux*|*monet*|*semantic*|*coui*)
                idmap2 dump --idmap-path "$f" > "$WORK/overlay/idmap_$name.txt" 2>&1
                ;;
        esac
    done
fi

say "[5/8] Settings / COUI runtime evidence"
{
    echo "--- top activity ---"
    dumpsys activity top 2>&1 | head -n 500
    echo
    echo "--- visible/resumed activities ---"
    dumpsys activity activities 2>/dev/null | grep -E 'mResumedActivity|topResumedActivity|Hist #[0-9]+|com.android.settings' | head -n 500
    echo
    echo "--- window focus ---"
    dumpsys window windows 2>/dev/null | grep -E 'mCurrentFocus|mFocusedApp|com.android.settings' | head -n 500
} > "$WORK/ui/settings-runtime.txt"

# Current visible UI only. Strip user-visible text/content descriptions but keep class/resource structure.
if have uiautomator; then
    RAWUI="$WORK/ui/current_raw.xml"
    uiautomator dump "$RAWUI" >/dev/null 2>&1
    if [ -f "$RAWUI" ]; then
        sed -E 's/text="[^"]*"/text=""/g;s/content-desc="[^"]*"/content-desc=""/g' "$RAWUI" > "$WORK/ui/current_sanitized.xml"
        rm -f "$RAWUI"
    fi
fi

say "[6/8] COE / LSPosed exception provenance"
{
    logcat -b all -d -v threadtime 2>/dev/null | grep -Ei \
      'one\.dot\.couiexpressive|CardHook|ListHook|MonetColorSpec2025Hook|QsLottieHook|AospMediaCardHook|mCardBackgroundColor|NoSuchFieldError|ClassNotFoundException' | tail -n 12000
} > "$WORK/logs/coe-logcat.txt"

for d in /data/adb/lspd/log /data/adb/lspd/logs /data/adb/modules/zygisk_lsposed/log; do
    [ -d "$d" ] || continue
    find "$d" -maxdepth 2 -type f 2>/dev/null | while IFS= read -r f; do
        grep -Ei \
          'one\.dot\.couiexpressive|CardHook|ListHook|MonetColorSpec2025Hook|QsLottieHook|AospMediaCardHook|mCardBackgroundColor|NoSuchFieldError|ClassNotFoundException' \
          "$f" 2>/dev/null >> "$WORK/logs/lsposed-filtered.txt" || true
    done
done

say "[7/8] SystemUI component evidence (privacy-filtered)"
{
    logcat -b all -d -v threadtime 2>/dev/null | grep -Ei \
      'QSIconViewProxy|SimpleQsClock|OplusVolumeDialogImpl|VolumePlatformBlurSession|VolumeSurfaceFactory|MediaPlayerCardPageRootView|SystemUIPlugin|lowGaussian|Notification.*Card|Lottie|DynamicColors|SchemeClock|UxMaterialDynamicColors' | tail -n 16000
} > "$WORK/logs/systemui-components.txt"

{
    dumpsys SurfaceFlinger --list 2>/dev/null | grep -Ei 'SystemUI|Quick|Shade|Notification|Volume|Media|Launcher|Settings' | head -n 1500
} > "$WORK/ui/surface-names.txt"

say "[8/8] Summary / archive"
{
    echo "ColorOS 17 × MD3E Runtime Evidence v1"
    echo "collector_policy=READ_ONLY"
    echo "theme_mutation=NO"
    echo "overlay_mutation=NO"
    echo "restart_apps=NO"
    echo "restart_systemui=NO"
    echo
    echo "Evidence targets:"
    echo "- UXDesign theme/style ownership and generated COUI XML state"
    echo "- actual package/APK provenance and hashes"
    echo "- OverlayManager/idmap runtime state"
    echo "- Settings current activity/view-resource structure without user text"
    echo "- COE NoSuchFieldError / classloader provenance from logs"
    echo "- SystemUI component-class activity without notification/media content dumps"
    echo
    echo "Note: current_sanitized.xml describes only the screen visible when the script runs."
} > "$WORK/README.txt"

tar -czf "$OUT" -C "$(dirname "$WORK")" "$(basename "$WORK")" 2>/dev/null
RC=$?
if [ "$RC" -eq 0 ] && [ -f "$OUT" ]; then
    if have sha256sum; then sha256sum "$OUT" > "$OUT.sha256"; fi
    chmod 0644 "$OUT" "$OUT.sha256" 2>/dev/null
    say "[✓] 完成：$OUT"
    say "直接把这个 tar.gz 发回来即可。"
    rm -rf "$WORK"
    exit 0
fi

say "[!] 打包失败，保留目录：$WORK"
exit 1
