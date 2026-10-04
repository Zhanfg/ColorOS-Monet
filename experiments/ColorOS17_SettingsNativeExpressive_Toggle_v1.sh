#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0
# Temporary ColorOS 17 native Settings Expressive gate probe.
# No arguments. No reboot. Property is non-persistent.

set +e
STATE=/data/local/tmp/ColorOS17_SettingsExpressive_gate.state
PROP=is_expressive_design_enabled

if [ "$(id -u 2>/dev/null)" != 0 ]; then
    echo "[!] 需要 root"
    exit 1
fi

current="$(getprop "$PROP" 2>/dev/null)"
if [ ! -f "$STATE" ]; then
    printf '%s\n' "$current" > "$STATE"
    chmod 0600 "$STATE" 2>/dev/null
fi

case "$current" in
    1|true|TRUE)
        previous="$(cat "$STATE" 2>/dev/null)"
        setprop "$PROP" "$previous" 2>/dev/null
        mode=RESTORE
        ;;
    *)
        setprop "$PROP" true 2>/dev/null
        mode=ENABLE
        ;;
esac

after="$(getprop "$PROP" 2>/dev/null)"
echo "mode=$mode"
echo "before=$current"
echo "after=$after"
echo "persistent=0"
echo "reboot_required=0"
echo
echo "请手动退出并重新打开“设置”观察。"
echo "本探针测试的是：OPlus XML/Preference + OPlus style + SettingsLib Expressive adapter。"
echo "它不会切换成 AOSP top_level_settings_expressive.xml。"
echo "脚本没有 force-stop Settings，也没有修改 Monet/theme JSON。"
echo "再次运行本脚本会恢复第一次运行前的 property 值。"
