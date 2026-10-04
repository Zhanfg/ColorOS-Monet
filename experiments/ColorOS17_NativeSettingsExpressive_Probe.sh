#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0
# ColorOS 17 native Settings Expressive reversible probe.
# No arguments. Run once to enable; run again to restore.
# No reboot / force-stop / overlay mutation / Monet theme-style mutation.

set +e
umask 077

PROP="is_expressive_design_enabled"
STATE_DIR="/data/adb/coloros-monet"
STATE="$STATE_DIR/native_settings_expressive_probe.state"
STAMP="$(date +%Y%m%d_%H%M%S 2>/dev/null)"
OUT="/sdcard/Download/ColorOS17_NativeSettingsExpressive_Probe_$STAMP.txt"
[ -d /sdcard/Download ] || OUT="/storage/emulated/0/Download/ColorOS17_NativeSettingsExpressive_Probe_$STAMP.txt"

say() { printf '%s\n' "$*" | tee -a "$OUT"; }

[ "$(id -u 2>/dev/null)" = 0 ] || {
    echo "[!] 需要 root。"
    exit 1
}

mkdir -p "$STATE_DIR" "$(dirname "$OUT")" 2>/dev/null

find_resetprop() {
    for p in \
        "$(command -v resetprop 2>/dev/null)" \
        /data/adb/ksu/bin/resetprop \
        /data/adb/magisk/resetprop \
        /system/bin/resetprop
    do
        [ -n "$p" ] && [ -x "$p" ] && { echo "$p"; return 0; }
    done
    return 1
}

RESETPROP="$(find_resetprop)"

write_prop() {
    value="$1"
    if [ -n "$RESETPROP" ]; then
        "$RESETPROP" "$PROP" "$value" >/dev/null 2>&1
        return $?
    fi
    setprop "$PROP" "$value" >/dev/null 2>&1
}

current_prop() { getprop "$PROP" 2>/dev/null; }

{
    echo "============================================================"
    echo " ColorOS 17 Native Settings Expressive Probe"
    echo "============================================================"
    echo "time=$(date '+%F %T %z' 2>/dev/null)"
    echo "model=$(getprop ro.product.model 2>/dev/null)"
    echo "sdk=$(getprop ro.build.version.sdk 2>/dev/null)"
    echo "build=$(getprop ro.build.display.id 2>/dev/null)"
    echo "resetprop=${RESETPROP:-unavailable}"
    echo "theme_before=$(settings get secure theme_customization_overlay_packages 2>/dev/null)"
    echo "property_before=$(current_prop)"
} > "$OUT"

if [ -f "$STATE" ]; then
    original="$(sed -n 's/^original=//p' "$STATE" | head -n 1)"
    [ -n "$original" ] || original=false
    say "[*] 检测到本探针上次已启用，开始恢复。"
    if write_prop "$original"; then
        rm -f "$STATE"
        say "[✓] 已恢复：$PROP=$original"
        say "[i] 不需要重启。把‘设置’从最近任务中关闭后重新打开即可观察恢复效果。"
    else
        say "[!] 恢复失败；状态文件保留：$STATE"
        exit 2
    fi
else
    original="$(current_prop)"
    [ -n "$original" ] || original=false
    {
        echo "original=$original"
        echo "build=$(getprop ro.build.display.id 2>/dev/null)"
        echo "created=$(date '+%F %T %z' 2>/dev/null)"
    } > "$STATE"
    chmod 0600 "$STATE" 2>/dev/null
    say "[*] 原值：$PROP=$original"
    if write_prop true; then
        say "[✓] 已临时启用 ColorOS/SettingsLib 原生 Expressive gate。"
        say "[i] 不需要重启。请把‘设置’从最近任务中关闭，再重新打开。"
        say "[i] 重点观察：设置首页、普通二级页、开关项、PreferenceCategory、搜索/更多按钮。"
        say "[i] 再运行一次本脚本即可恢复原值。"
    else
        say "[!] 无法写入系统属性。"
        rm -f "$STATE"
        exit 3
    fi
fi

{
    echo "property_after=$(current_prop)"
    echo "theme_after=$(settings get secure theme_customization_overlay_packages 2>/dev/null)"
    echo "state_file_present=$([ -f "$STATE" ] && echo 1 || echo 0)"
    echo "safety=no_reboot,no_force_stop,no_overlay_mutation,no_theme_style_mutation"
} >> "$OUT"

say "[✓] 日志：$OUT"
