#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0
# ColorOS 17 MD3E runtime evidence collector v1.
# Read-only; no restart, no overlay/theme mutation, no arguments.

set +e

TS="$(date +%Y%m%d_%H%M%S 2>/dev/null)"
[ -n "$TS" ] || TS=unknown
OUT="/sdcard/Download/ColorOS17_MD3E_RuntimeEvidence_v1_$TS"
ARCHIVE="$OUT.tar.gz"
mkdir -p "$OUT" || exit 1

have() { command -v "$1" >/dev/null 2>&1; }

{
    echo "time=$(date '+%F %T %z' 2>/dev/null)"
    echo "model=$(getprop ro.product.model 2>/dev/null)"
    echo "device=$(getprop ro.product.device 2>/dev/null)"
    echo "sdk=$(getprop ro.build.version.sdk 2>/dev/null)"
    echo "display=$(getprop ro.build.display.id 2>/dev/null)"
    echo "oplusrom=$(getprop ro.build.version.oplusrom 2>/dev/null)"
    echo "fingerprint=$(getprop ro.build.fingerprint 2>/dev/null)"
    echo "theme_json=$(settings get secure theme_customization_overlay_packages 2>/dev/null)"
    echo "material_blur=$(getprop persist.sys.oplus.material_blur_switch 2>/dev/null)"
} > "$OUT/device_theme.txt"

{
    echo "--- focused window/activity ---"
    dumpsys window 2>/dev/null | grep -E 'mCurrentFocus|mFocusedApp|mObscuringWindow' | head -n 80
    echo
    dumpsys activity activities 2>/dev/null | grep -E       'mResumedActivity|ResumedActivity|OplusSettingsHomepageActivity|SettingsHomepageActivity|SubSettings|DeviceInfoFragment' | head -n 300
} > "$OUT/active_ui.txt"

{
    echo "--- Settings / SystemUI / plugin package paths ---"
    for pkg in com.android.settings com.android.systemui com.oplus.uxdesign one.dot.couiexpressive; do
        echo "===== $pkg ====="
        pm path "$pkg" 2>&1
        dumpsys package "$pkg" 2>/dev/null | grep -E           'versionName=|versionCode=|codePath=|resourcePath=|overlayTarget=|isStatic=' | head -n 80
    done
} > "$OUT/packages.txt"

{
    echo "--- relevant DeviceConfig / Settings flags ---"
    if have device_config; then
        device_config list 2>/dev/null | grep -Ei           'expressive|material|settingslib|settings_ui|systemui|monet|dynamic.?color' | head -n 1200
    fi
    settings list secure 2>/dev/null | grep -Ei       'theme|monet|material|expressive|wallpaper|color' | head -n 800
    settings list global 2>/dev/null | grep -Ei       'theme|monet|material|expressive|wallpaper|color' | head -n 800
} > "$OUT/feature_flags.txt"

{
    echo "--- OverlayManager ---"
    if have timeout; then
        timeout 8 cmd overlay list --user 0 2>&1
    else
        cmd overlay list --user 0 2>&1
    fi
} > "$OUT/overlay_list.txt"

{
    echo "--- Settings process provenance ---"
    pid="$(pidof com.android.settings 2>/dev/null | awk '{print $1}')"
    echo "settings_pid=$pid"
    if [ -n "$pid" ] && [ -r "/proc/$pid/maps" ]; then
        grep -Ei 'Settings|coui|oplus|framework|lsposed|lsp|xposed|couiexpressive' "/proc/$pid/maps" | head -n 2000
    fi
    echo
    echo "--- SystemUI process provenance ---"
    pid="$(pidof com.android.systemui 2>/dev/null | awk '{print $1}')"
    echo "systemui_pid=$pid"
    if [ -n "$pid" ] && [ -r "/proc/$pid/maps" ]; then
        grep -Ei 'SystemUI|plugin|coui|oplus|framework|lsposed|lsp|xposed|couiexpressive' "/proc/$pid/maps" | head -n 3000
    fi
} > "$OUT/process_maps.txt"

{
    logcat -b all -d -v threadtime 2>/dev/null | grep -Ei       'COUICustomListSelectedLinearLayout|COUICardListSelectedItemLayout|mCardBackgroundColor|NoSuchFieldError|CardHook|ListHook|MonetColorSpec2025Hook|QsLottieHook|AospMediaCardHook|SimpleQsClock|OplusVolumeDialogImpl|ThemeOverlayController|SPEC_2026|one\.dot\.couiexpressive' | tail -n 12000
} > "$OUT/logcat_structural.txt"

{
    echo "READ_ONLY=1"
    echo "NO_RESTART=1"
    echo "NO_THEME_MUTATION=1"
    echo "NO_OVERLAY_MUTATION=1"
    echo
    echo "Open the target page before running this collector when a specific"
    echo "Settings/SystemUI runtime binding needs to be captured."
} > "$OUT/README.txt"

tar -czf "$ARCHIVE" -C "$(dirname "$OUT")" "$(basename "$OUT")" 2>/dev/null
if [ -f "$ARCHIVE" ]; then
    if have sha256sum; then
        sha256sum "$ARCHIVE" > "$ARCHIVE.sha256"
    fi
    chmod 0644 "$ARCHIVE" "$ARCHIVE.sha256" 2>/dev/null
    echo "[✓] $ARCHIVE"
else
    echo "[!] 打包失败，原始目录保留：$OUT"
    exit 2
fi
