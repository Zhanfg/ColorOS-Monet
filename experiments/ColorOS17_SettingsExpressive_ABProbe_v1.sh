#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0
# ColorOS 17 native Settings Expressive A/B probe.
# No arguments. No reboot. Reversible.
# This intentionally restarts only com.android.settings to force Activity recreation.
# It does NOT modify Monet/theme JSON, OverlayManager, SystemUI, Launcher or persistent props.

set +e
umask 077

PROP=is_expressive_design_enabled
STAMP="$(date +%Y%m%d_%H%M%S 2>/dev/null)"
[ -n "$STAMP" ] || STAMP=unknown
BASE=/sdcard/Download
[ -d "$BASE" ] || BASE=/storage/emulated/0/Download
[ -d "$BASE" ] || BASE="$(pwd)"
WORK="/data/local/tmp/ColorOS17_SettingsExpressive_ABProbe_v1_$STAMP"
OUT="$BASE/ColorOS17_SettingsExpressive_ABProbe_v1_$STAMP.tar.gz"

mkdir -p "$WORK/A_native_off" "$WORK/B_native_on" "$WORK/restored" || exit 1

say() { printf '%s\n' "$*"; }
have() { command -v "$1" >/dev/null 2>&1; }

[ "$(id -u 2>/dev/null)" = 0 ] || {
    say "[!] 需要 root。"
    exit 1
}

ORIGINAL="$(getprop "$PROP" 2>/dev/null)"
printf '%s\n' "$ORIGINAL" > "$WORK/original_property.txt"

restore() {
    setprop "$PROP" "$ORIGINAL" 2>/dev/null
}
trap restore 0 1 2 15

capture_state() {
    dir="$1"
    label="$2"

    {
        echo "label=$label"
        echo "time=$(date '+%F %T %z' 2>/dev/null)"
        echo "property=$(getprop "$PROP" 2>/dev/null)"
        echo "sdk=$(getprop ro.build.version.sdk 2>/dev/null)"
        echo "display=$(getprop ro.build.display.id 2>/dev/null)"
        echo "theme_json=$(settings get secure theme_customization_overlay_packages 2>/dev/null)"
        echo
        echo "--- activity ---"
        dumpsys activity activities 2>/dev/null | grep -E             'mResumedActivity|topResumedActivity|OplusSettingsHomepageActivity|OplusTopLevelSettings|SettingsHomepageActivity|TopLevelSettings' | head -n 300
        echo
        echo "--- window ---"
        dumpsys window windows 2>/dev/null | grep -E             'mCurrentFocus|mFocusedApp|Settings' | head -n 160
        echo
        echo "--- flag sources ---"
        echo "sysprop=$(getprop "$PROP" 2>/dev/null)"
        if have device_config; then
            echo "device_config_android_settings=$(device_config get android_settings is_expressive_design_enabled 2>/dev/null)"
        fi
    } > "$dir/state.txt"

    screencap -p "$dir/screen.png" >/dev/null 2>&1

    if have uiautomator; then
        uiautomator dump "$dir/window.xml" >/dev/null 2>&1
    fi
}

recreate_settings() {
    # This is the only process mutation in the experiment.
    am force-stop com.android.settings >/dev/null 2>&1
    sleep 1
    am start -W -a android.settings.SETTINGS >/dev/null 2>&1
    sleep 3
}

say "============================================================"
say " ColorOS 17 Settings native Expressive A/B probe"
say " 只重启 Settings；不重启系统/SystemUI；不改主题 JSON"
say "============================================================"
say "[0/5] original $PROP='$ORIGINAL'"

say "[1/5] A: native Expressive debug override = false"
setprop "$PROP" false 2>/dev/null
recreate_settings
capture_state "$WORK/A_native_off" "A_NATIVE_OFF"

say "[2/5] B: native Expressive debug override = true"
setprop "$PROP" true 2>/dev/null
recreate_settings
capture_state "$WORK/B_native_on" "B_NATIVE_ON"

say "[3/5] Capture focused Settings logs"
{
    logcat -b all -d -v threadtime 2>/dev/null | grep -Ei         'SettingsThemeHelper|SettingsPreferenceGroupAdapter|OplusTopLevelSettings|OplusSettingsHomepageActivity|Expressive|COUICard|CardHook|ListHook|NoSuchFieldError|mCardBackgroundColor' | tail -n 10000
} > "$WORK/settings_logcat.txt"

say "[4/5] Restore original property and Settings state"
restore
recreate_settings
capture_state "$WORK/restored" "RESTORED"
trap - 0 1 2 15

{
    echo "collector=ColorOS17_SettingsExpressive_ABProbe_v1"
    echo "original_property=$ORIGINAL"
    echo "restored_property=$(getprop "$PROP" 2>/dev/null)"
    echo "reboot_required=0"
    echo "mutated_process=com.android.settings only"
    echo "theme_json_mutated=0"
    echo "overlay_manager_mutated=0"
    echo "systemui_restarted=0"
    echo "launcher_restarted=0"
    echo
    echo "Expected interpretation:"
    echo "- A/B differ materially -> native Settings Expressive gate is live on this ColorOS build."
    echo "- A/B same -> inspect flag/activity/resource runtime evidence before any custom UI implementation."
    echo "- restored/ should match the user's original gate state."
} > "$WORK/README.txt"

find "$WORK" -type f -print0 2>/dev/null | sort -z | xargs -0 sha256sum > "$WORK/SHA256SUMS" 2>/dev/null

say "[5/5] Package result"
tar -czf "$OUT" -C "$WORK" . 2>/dev/null || {
    say "[!] 打包失败，保留：$WORK"
    exit 2
}
sha256sum "$OUT" > "$OUT.sha256" 2>/dev/null
chmod 0644 "$OUT" "$OUT.sha256" 2>/dev/null
rm -rf "$WORK"

say "[✓] $OUT"
say "[✓] 已恢复 $PROP='$(getprop "$PROP" 2>/dev/null)'"
