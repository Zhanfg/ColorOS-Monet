#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0

MODDIR=${0%/*}
STATE_DIR=/data/adb/coloros-monet
STATE_FILE="$STATE_DIR/config.conf"
TARGETS="$MODDIR/payload/targets.tsv"

mkdir -p "$STATE_DIR"
[ -f "$STATE_FILE" ] || cp -f "$MODDIR/config/default.conf" "$STATE_FILE"

wait_key() {
    while :; do
        event="$(getevent -qlc 1 2>/dev/null)"
        case "$event" in
            *KEY_VOLUMEUP*DOWN*) return 0 ;;
            *KEY_VOLUMEDOWN*DOWN*) return 1 ;;
        esac
    done
}

set_flag() {
    key="$1" value="$2"
    tmp="$STATE_FILE.tmp.$$"
    awk -F= -v k="$key" -v v="$value" '
        BEGIN { found=0 }
        $1==k { print k "=" v; found=1; next }
        { print }
        END { if (!found) print k "=" v }
    ' "$STATE_FILE" > "$tmp" && mv -f "$tmp" "$STATE_FILE"
}

echo "ColorOS Monet 覆盖开关"
echo "对每一项：音量+启用，音量-禁用"

TAB=$(printf '\t')
while IFS="$TAB" read -r key target overlay _apk; do
    case "$key" in ''|'#'*) continue ;; esac
    echo ""
    echo "[$key] $target"
    echo "音量+：启用　音量-：禁用"
    if wait_key; then
        set_flag "$key" 1
        cmd overlay enable --user 0 "$overlay" >/dev/null 2>&1
        echo "已启用：$key"
    else
        set_flag "$key" 0
        cmd overlay disable --user 0 "$overlay" >/dev/null 2>&1
        echo "已禁用：$key"
    fi
done < "$TARGETS"

chmod 0600 "$STATE_FILE" 2>/dev/null
echo ""
echo "配置已保存。部分页面需要强制停止目标应用或重启后刷新。"
