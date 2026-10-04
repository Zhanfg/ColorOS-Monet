#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0

MODDIR=${0%/*}
STATE_DIR=/data/adb/coloros-monet
STATE_FILE="$STATE_DIR/config.conf"
SEMANTIC_MANIFEST="$MODDIR/payload/semantic-accent-manifest.tsv"
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

apply_semantic_now() {
    enabled="$1"
    [ -f "$SEMANTIC_MANIFEST" ] || return 0
    TAB=$(printf '\t')
    while IFS="$TAB" read -r key target overlay apk count; do
        case "$key" in ''|'#'*) continue ;; esac
        [ "$key" = key ] && continue
        if [ "$enabled" = 1 ]; then
            cmd overlay enable --user 0 "$overlay" >/dev/null 2>&1 || true
            cmd overlay set-priority --user 0 "$overlay" highest >/dev/null 2>&1 || true
        else
            cmd overlay disable --user 0 "$overlay" >/dev/null 2>&1 || true
        fi
    done < "$SEMANTIC_MANIFEST"
}

run_doctor() {
    if [ -x "$DOCTOR" ]; then
        "$DOCTOR"
    else
        echo "[错误] ColorOS 17 MD3E 诊断器不存在或不可执行：$DOCTOR"
        return 1
    fi
}

echo "ColorOS 17 Monet / MD3E"
echo "音量+：切换 MD3E 语义动态色"
echo "音量-：导出只读诊断报告"

if ! wait_key; then
    run_doctor
    exit $?
fi

current="$(sed -n 's/^md3e_semantic=//p' "$STATE_FILE" | tail -n 1)"
if [ "$current" = 1 ]; then
    set_flag md3e_semantic 0
    apply_semantic_now 0
    echo "[已关闭] MD3E 语义动态色"
else
    set_flag md3e_semantic 1
    apply_semantic_now 1
    echo "[已启用] MD3E 语义动态色"
fi

chmod 0600 "$STATE_FILE" 2>/dev/null
echo "未重启任何应用、SystemUI 或系统服务。"
