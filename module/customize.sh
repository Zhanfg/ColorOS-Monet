#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0
# shellcheck disable=SC2154
# MODPATH is provided by the module installer.

STATE_DIR=/data/adb/coloros-monet
STATE_FILE="$STATE_DIR/config.conf"
TARGETS="$MODPATH/payload/targets.tsv"
OVERLAY_SRC="$MODPATH/payload/overlays"
OVERLAY_DST="$MODPATH/system/product/overlay"

ui_print "- ColorOS Monet clean-room installer"

SDK="$(getprop ro.build.version.sdk 2>/dev/null)"
case "$SDK" in
    ''|*[!0-9]*) abort "! 无法读取 Android SDK 版本" ;;
esac
[ "$SDK" -ge 31 ] || abort "! 需要 Android 12 / SDK 31 或更高版本"

mkdir -p "$STATE_DIR" "$OVERLAY_DST" || abort "! 无法创建模块目录"
if [ ! -f "$STATE_FILE" ]; then
    cp -f "$MODPATH/config/default.conf" "$STATE_FILE" || abort "! 无法初始化配置"
fi
chmod 0600 "$STATE_FILE" 2>/dev/null

read_flag() {
    key="$1"
    value="$(sed -n "s/^${key}=//p" "$STATE_FILE" | tail -n 1)"
    [ "$value" = 1 ]
}

install_one() {
    key="$1" apk="$2"
    src="$OVERLAY_SRC/$apk"
    dst="$OVERLAY_DST/$apk"

    [ -f "$src" ] || {
        ui_print "! 缺少构建产物：$apk"
        return 1
    }
    if ! read_flag "$key"; then
        rm -f "$dst"
        ui_print "- 已按配置禁用：$key"
        return 0
    fi
    cp -f "$src" "$dst" || return 1
    chmod 0644 "$dst" 2>/dev/null
    ui_print "- 已加入覆盖：$key"
}

TAB=$(printf '\t')
while IFS="$TAB" read -r key _target _overlay apk; do
    case "$key" in ''|'#'*) continue ;; esac
    install_one "$key" "$apk" || abort "! 安装 $key 覆盖失败"
done < "$TARGETS"

rm -rf "$MODPATH/payload/overlays"
ui_print "- 安装完成。重启后由 service.sh 启用并检查覆盖状态。"
