#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0

MODDIR=${0%/*}
STATE_DIR=/data/adb/coloros-monet
STATE_FILE="$STATE_DIR/config.conf"
TARGETS="$MODDIR/payload/targets.tsv"
DOCTOR="$MODDIR/bin/coloros-monet-doctor"

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
    key="$1"
    value="$2"
    tmp="$STATE_FILE.tmp.$$"
    awk -F= -v k="$key" -v v="$value" '
        BEGIN { found=0 }
        $1==k { print k "=" v; found=1; next }
        { print }
        END { if (!found) print k "=" v }
    ' "$STATE_FILE" > "$tmp" && mv -f "$tmp" "$STATE_FILE"
}

package_present() {
    pm path "$1" 2>/dev/null | grep -q '^package:'
}

overlay_enabled() {
    package="$1"
    cmd overlay list --user 0 2>/dev/null | grep -F "$package" | \
        grep -Eq '\[x\]|STATE_ENABLED|STATE_ENABLED_IMMUTABLE'
}

run_doctor() {
    if [ -x "$DOCTOR" ]; then
        "$DOCTOR"
    else
        echo "[错误] X 诊断器不存在或不可执行：$DOCTOR"
        return 1
    fi
}

echo "ColorOS Monet 控制台"
echo "音量+：管理覆盖开关"
echo "音量-：导出 X 只读诊断报告"
if ! wait_key; then
    run_doctor
    exit $?
fi

echo ""
echo "对每一项：音量+启用，音量-禁用"

TAB=$(printf '\t')
while IFS="$TAB" read -r key target overlay _apk; do
    case "$key" in ''|'#'*) continue ;; esac
    echo ""
    echo "[$key] $target"
    echo "音量+：启用　音量-：禁用"
    if wait_key; then
        if ! package_present "$target"; then
            set_flag "$key" 0
            echo "[失败] 目标应用未安装：$target"
            [ "$key" = x ] && run_doctor
            continue
        fi
        if ! package_present "$overlay"; then
            set_flag "$key" 0
            echo "[失败] 覆盖包未被系统识别：$overlay"
            [ "$key" = x ] && run_doctor
            continue
        fi

        output="$(cmd overlay enable --user 0 "$overlay" 2>&1)"
        rc=$?
        [ -n "$output" ] && echo "$output"
        sleep 1
        if [ "$rc" -eq 0 ] && overlay_enabled "$overlay"; then
            set_flag "$key" 1
            echo "[已启用] $key"
        else
            cmd overlay disable --user 0 "$overlay" >/dev/null 2>&1
            set_flag "$key" 0
            echo "[失败] OverlayManager 未接受覆盖：$key"
            [ "$key" = x ] && run_doctor
        fi
    else
        output="$(cmd overlay disable --user 0 "$overlay" 2>&1)"
        rc=$?
        [ -n "$output" ] && echo "$output"
        set_flag "$key" 0
        if [ "$rc" -eq 0 ]; then
            echo "[已禁用] $key"
        else
            echo "[警告] 已保存禁用配置，但系统命令返回 $rc：$key"
        fi
    fi
done < "$TARGETS"

chmod 0600 "$STATE_FILE" 2>/dev/null
echo ""
echo "配置已保存。脚本未重启目标应用或系统音频/图形服务。"
