#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0
# shellcheck disable=SC2154
# MODPATH is provided by the module installer.

STATE_DIR=/data/adb/coloros-monet
STATE_FILE="$STATE_DIR/config.conf"
TARGETS="$MODPATH/payload/targets.tsv"
OVERLAY_SRC="$MODPATH/payload/overlays"
OVERLAY_DST="$MODPATH/system/product/overlay"
NATIVE_SRC="$MODPATH/payload/native-foundation"
NATIVE_MANIFEST="$NATIVE_SRC/native-foundation-manifest.tsv"
DOCTOR="$MODPATH/bin/coloros-monet-doctor"

ui_print "- ColorOS Monet / MD3E native-first installer"

SDK="$(getprop ro.build.version.sdk 2>/dev/null)"
case "$SDK" in
    ''|*[!0-9]*) abort "! 无法读取 Android SDK 版本" ;;
esac
[ "$SDK" -ge 31 ] || abort "! 需要 Android 12 / SDK 31 或更高版本"

mkdir -p "$STATE_DIR" "$OVERLAY_DST" || abort "! 无法创建模块目录"
if [ ! -f "$STATE_FILE" ]; then
    cp -f "$MODPATH/config/default.conf" "$STATE_FILE" || abort "! 无法初始化配置"
fi
if ! grep -q '^native_expressive=' "$STATE_FILE" 2>/dev/null; then
    printf '\nnative_expressive=1\n' >> "$STATE_FILE"
fi
chmod 0600 "$STATE_FILE" 2>/dev/null
[ -f "$DOCTOR" ] && chmod 0755 "$DOCTOR" 2>/dev/null

read_flag() {
    key="$1"
    value="$(sed -n "s/^${key}=//p" "$STATE_FILE" | tail -n 1)"
    [ "$value" = 1 ]
}

is_coloros17() {
    [ "$SDK" -ge 37 ] || return 1
    oplusrom="$(getprop ro.build.version.oplusrom 2>/dev/null)"
    display="$(getprop ro.build.display.id 2>/dev/null)"
    case "$oplusrom $display" in
        *17.*|*17_*) return 0 ;;
    esac
    return 1
}

install_native_foundation() {
    [ -d "$NATIVE_SRC" ] || return 0
    [ -f "$NATIVE_MANIFEST" ] || {
        ui_print "! 缺少 ColorOS 17 native foundation 清单"
        return 1
    }

    if ! is_coloros17; then
        ui_print "- 非 ColorOS 17：跳过 native-first 兼容层"
        return 0
    fi

    ui_print "- 检测到 ColorOS 17：安装 native-first 基础层"
    TAB=$(printf '\t')
    while IFS="$TAB" read -r _key _target _overlay apk _count; do
        case "$_key" in ''|'#'*) continue ;; esac
        [ "$_key" = key ] && continue
        src="$NATIVE_SRC/$apk"
        [ -f "$src" ] || {
            ui_print "! native foundation 缺少：$apk"
            return 1
        }
        cp -f "$src" "$OVERLAY_DST/$apk" || return 1
        chmod 0644 "$OVERLAY_DST/$apk" 2>/dev/null
    done < "$NATIVE_MANIFEST"
    return 0
}

install_one() {
    key="$1"
    apk="$2"
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

install_native_foundation || abort "! 安装 ColorOS 17 native-first 基础层失败"

rm -rf "$MODPATH/payload/overlays" "$MODPATH/payload/native-foundation"
ui_print "- 已安装 X 只读诊断器，可从模块操作菜单导出报告。"
ui_print "- 安装完成。重启后由 service.sh 验证动态覆盖与 ColorOS 17 native-first 基础层状态。"
