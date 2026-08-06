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
trap 'rmdir "$LOCK" 2>/dev/null' 0

count=0
while [ "$(getprop sys.boot_completed 2>/dev/null)" != 1 ] && [ "$count" -lt 180 ]; do
    sleep 1
    count=$((count + 1))
done

read_flag() {
    key="$1"
    [ "$(sed -n "s/^${key}=//p" "$STATE_FILE" 2>/dev/null | tail -n 1)" = 1 ]
}

package_present() {
    pm path "$1" 2>/dev/null | grep -q '^package:'
}

overlay_enabled() {
    package="$1"
    cmd overlay list --user 0 2>/dev/null | grep -F "$package" | \
        grep -Eq '\[x\]|STATE_ENABLED|STATE_ENABLED_IMMUTABLE'
}

package_version() {
    dumpsys package "$1" 2>/dev/null | sed -n 's/.*versionName=//p' | head -n 1
}

apply_requested_overlay() {
    key="$1"
    target="$2"
    overlay="$3"

    echo "[$key] target=$target overlay=$overlay requested=1"
    if ! package_present "$target"; then
        echo "guard=target_missing"
        cmd overlay disable --user 0 "$overlay" 2>&1
        return 1
    fi
    if ! package_present "$overlay"; then
        echo "guard=overlay_missing"
        return 1
    fi

    target_version="$(package_version "$target")"
    echo "target_version=${target_version:-unknown}"
    if [ "$key" = x ] && [ "$target_version" != 12.13.0 ]; then
        echo "compatibility_warning=reviewed_for_12.13.0"
    fi

    echo "enable_output_begin"
    cmd overlay enable --user 0 "$overlay" 2>&1
    enable_rc=$?
    echo "enable_output_end"
    echo "enable_exit_code=$enable_rc"
    sleep 1

    if [ "$enable_rc" -ne 0 ] || ! overlay_enabled "$overlay"; then
        echo "guard=enable_rejected"
        cmd overlay disable --user 0 "$overlay" 2>&1
        return 1
    fi

    echo "guard=accepted"
    cmd overlay list --user 0 2>&1 | grep -F "$overlay" || true
    return 0
}

apply_disabled_overlay() {
    key="$1"
    target="$2"
    overlay="$3"
    echo "[$key] target=$target overlay=$overlay requested=0"
    cmd overlay disable --user 0 "$overlay" 2>&1
    echo "guard=disabled_by_configuration"
}

{
    echo "time=$(date '+%Y-%m-%d %H:%M:%S %z' 2>/dev/null)"
    echo "sdk=$(getprop ro.build.version.sdk 2>/dev/null)"
    echo "build=$(getprop ro.build.display.id 2>/dev/null)"
    echo "boot_completed=$(getprop sys.boot_completed 2>/dev/null)"
    echo "policy=no_app_or_system_service_restart"
    echo "--- overlays ---"
    TAB=$(printf '\t')
    while IFS="$TAB" read -r key target overlay _apk; do
        case "$key" in ''|'#'*) continue ;; esac
        if read_flag "$key"; then
            apply_requested_overlay "$key" "$target" "$overlay"
        else
            apply_disabled_overlay "$key" "$target" "$overlay"
        fi
        pm path "$target" 2>&1
        pm path "$overlay" 2>&1
        echo
    done < "$TARGETS"
} > "$LOG" 2>&1

chmod 0644 "$LOG" 2>/dev/null
exit 0
