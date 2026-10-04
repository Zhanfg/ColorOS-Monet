#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0
# shellcheck disable=SC2154

STATE_DIR=/data/adb/coloros-monet
STATE_FILE="$STATE_DIR/config.conf"
OVERLAY_DST="$MODPATH/system/product/overlay"
SEMANTIC_SRC="$MODPATH/payload/semantic-accent"
SEMANTIC_MANIFEST="$SEMANTIC_SRC/semantic-accent-manifest.tsv"
DOCTOR="$MODPATH/bin/coloros-monet-doctor"

ui_print "- ColorOS 17 Monet / MD3E native-first installer"

SDK="$(getprop ro.build.version.sdk 2>/dev/null)"
DISPLAY="$(getprop ro.build.display.id 2>/dev/null)"
OPLUSROM="$(getprop ro.build.version.oplusrom 2>/dev/null)"

[ "$SDK" = 37 ] || abort "! 本构建仅适用于 Android 17 / SDK 37"
case "$DISPLAY $OPLUSROM" in
    *17.0*|*ColorOS*17*|*OxygenOS*17*) ;;
    *) abort "! 未确认 ColorOS/OxygenOS 17 构建，停止安装" ;;
esac

[ -f "$SEMANTIC_MANIFEST" ] || abort "! 缺少 semantic accent manifest"

mkdir -p "$STATE_DIR" "$OVERLAY_DST" || abort "! 无法创建模块目录"
if [ ! -f "$STATE_FILE" ]; then
    cp -f "$MODPATH/config/default.conf" "$STATE_FILE" || abort "! 无法初始化配置"
fi
if ! grep -q '^md3e_semantic=' "$STATE_FILE" 2>/dev/null; then
    # Migration must preserve the v0.2.0 safe default: opt-in only.
    printf '\nmd3e_semantic=0\n' >> "$STATE_FILE"
fi
chmod 0600 "$STATE_FILE" 2>/dev/null
[ -f "$DOCTOR" ] && chmod 0755 "$DOCTOR" 2>/dev/null

ui_print "- 安装 ColorOS 17 MD3E semantic accent 层"
TAB=$(printf '\t')
while IFS="$TAB" read -r key target overlay apk count; do
    case "$key" in ''|'#'*) continue ;; esac
    [ "$key" = key ] && continue
    src="$SEMANTIC_SRC/$apk"
    [ -f "$src" ] || abort "! 缺少 semantic overlay：$apk"
    cp -f "$src" "$OVERLAY_DST/$apk" || abort "! 无法安装：$apk"
    chmod 0644 "$OVERLAY_DST/$apk" 2>/dev/null
done < "$SEMANTIC_MANIFEST"

rm -rf "$MODPATH/payload/semantic-accent"
ui_print "- 不修改当前 ColorOS 主题 style；只接入现有 system_primary 语义色"
ui_print "- 不重启应用、SystemUI 或系统服务；覆盖在正常重启后生效"
