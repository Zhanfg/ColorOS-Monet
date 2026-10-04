#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0

MODDIR=${0%/*}
STATE_DIR=/data/adb/coloros-monet
STATE_FILE="$STATE_DIR/config.conf"
SEMANTIC_MANIFEST="$MODDIR/payload/semantic-accent-manifest.tsv"
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

apply_semantic_overlay() {
    key="$1"
    target="$2"
    overlay="$3"
    apk="$4"
    count="$5"

    echo "[$key] target=$target overlay=$overlay apk=$apk entries=$count"
    if ! package_present "$target"; then
        echo "guard=target_missing"
        return 1
    fi
    if ! package_present "$overlay"; then
        echo "guard=overlay_missing"
        return 1
    fi

    cmd overlay enable --user 0 "$overlay" 2>&1
    enable_rc=$?
    echo "enable_exit_code=$enable_rc"

    cmd overlay set-priority --user 0 "$overlay" highest 2>&1
    priority_rc=$?
    echo "priority_exit_code=$priority_rc"

    sleep 1
    if [ "$enable_rc" -ne 0 ] || ! overlay_enabled "$overlay"; then
        echo "guard=enable_rejected"
        return 1
    fi

    echo "guard=accepted"
    cmd overlay list --user 0 2>/dev/null | grep -F "$overlay" || true
    return 0
}

{
    echo "time=$(date '+%Y-%m-%d %H:%M:%S %z' 2>/dev/null)"
    echo "sdk=$(getprop ro.build.version.sdk 2>/dev/null)"
    echo "build=$(getprop ro.build.display.id 2>/dev/null)"
    echo "boot_completed=$(getprop sys.boot_completed 2>/dev/null)"
    echo "policy=no_app_or_system_service_restart"
    echo "theme_policy=do_not_mutate_theme_style"
    echo "--- md3e-semantic-accent ---"

    if [ ! -f "$SEMANTIC_MANIFEST" ]; then
        echo "semantic_accent_manifest=absent"
    elif read_flag md3e_semantic; then
        TAB=$(printf '\t')
        while IFS="$TAB" read -r key target overlay apk count; do
            case "$key" in ''|'#'*) continue ;; esac
            [ "$key" = key ] && continue
            apply_semantic_overlay "$key" "$target" "$overlay" "$apk" "$count" || true
            echo
        done < "$SEMANTIC_MANIFEST"
    else
        TAB=$(printf '\t')
        while IFS="$TAB" read -r key target overlay apk count; do
            case "$key" in ''|'#'*) continue ;; esac
            [ "$key" = key ] && continue
            cmd overlay disable --user 0 "$overlay" 2>&1
            echo "[$key] guard=disabled_by_configuration"
        done < "$SEMANTIC_MANIFEST"
    fi
} > "$LOG" 2>&1

chmod 0644 "$LOG" 2>/dev/null
exit 0
