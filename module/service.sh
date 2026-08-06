#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0

MODDIR=${0%/*}
STATE_DIR=/data/adb/coloros-monet
STATE_FILE="$STATE_DIR/config.conf"
TARGETS="$MODDIR/payload/targets.tsv"
LOG="$STATE_DIR/overlay-status.log"
LOCK="$STATE_DIR/service.lock"

mkdir -p "$STATE_DIR" || exit 0
mkdir "$LOCK" 2>/dev/null || exit 0
trap 'rmdir "$LOCK" 2>/dev/null' EXIT

count=0
while [ "$(getprop sys.boot_completed 2>/dev/null)" != 1 ] && [ "$count" -lt 180 ]; do
    sleep 1
    count=$((count + 1))
done

read_flag() {
    key="$1"
    [ "$(sed -n "s/^${key}=//p" "$STATE_FILE" 2>/dev/null | tail -n 1)" = 1 ]
}

{
    echo "time=$(date '+%Y-%m-%d %H:%M:%S' 2>/dev/null)"
    echo "sdk=$(getprop ro.build.version.sdk 2>/dev/null)"
    echo "--- overlays ---"
    TAB=$(printf '\t')
    while IFS="$TAB" read -r key target overlay apk; do
        case "$key" in ''|'#'*) continue ;; esac
        if read_flag "$key"; then
            cmd overlay enable --user 0 "$overlay" 2>&1
        else
            cmd overlay disable --user 0 "$overlay" 2>&1
        fi
        echo "[$key] target=$target overlay=$overlay requested=$(read_flag "$key" && echo 1 || echo 0)"
        pm path "$target" 2>&1
        pm path "$overlay" 2>&1
        cmd overlay list --user 0 2>&1 | grep -F "$overlay" || echo "overlay_state=not_listed"
    done < "$TARGETS"
} > "$LOG" 2>&1

exit 0
