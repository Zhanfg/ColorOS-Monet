#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0
# ColorOS 17 native Monet-style bridge.
# Default action: apply EXPRESSIVE. Optional internal actions: restore/status/toggle.

STATE_DIR=/data/adb/coloros-monet
PREV_STYLE_FILE="$STATE_DIR/previous_theme_style"
KEY=theme_customization_overlay_packages
TARGET_STYLE=EXPRESSIVE
MODE="${1:-apply}"

mkdir -p "$STATE_DIR" 2>/dev/null

read_json() {
    settings get secure "$KEY" 2>/dev/null
}

extract_style() {
    printf '%s' "$1" | sed -n 's/.*"android.theme.customization.theme_style":"\([^"]*\)".*/\1/p'
}

set_style_in_json() {
    json="$1"
    style="$2"

    case "$json" in
        ''|null)
            ts="$(date +%s 2>/dev/null)000"
            printf '{"android.theme.customization.color_source":"home_wallpaper","android.theme.customization.theme_style":"%s","_applied_timestamp":%s,"material_you_overlay_enable":1,"android.theme.customization.color_both":"0"}' "$style" "$ts"
            return
            ;;
    esac

    if printf '%s' "$json" | grep -q '"android.theme.customization.theme_style"'; then
        json="$(printf '%s' "$json" | sed "s/\"android.theme.customization.theme_style\":\"[^\"]*\"/\"android.theme.customization.theme_style\":\"$style\"/")"
    else
        json="$(printf '%s' "$json" | sed "s/}$/,\"android.theme.customization.theme_style\":\"$style\"}/")"
    fi

    if printf '%s' "$json" | grep -q '"material_you_overlay_enable"'; then
        json="$(printf '%s' "$json" | sed 's/"material_you_overlay_enable":[01]/"material_you_overlay_enable":1/')"
    else
        json="$(printf '%s' "$json" | sed 's/}$/,"material_you_overlay_enable":1}/')"
    fi

    printf '%s' "$json"
}

apply_style() {
    style="$1"
    current="$(read_json)"
    current_style="$(extract_style "$current")"
    [ -n "$current_style" ] || current_style=TONAL_SPOT

    if [ "$style" = "$TARGET_STYLE" ] && [ "$current_style" != "$TARGET_STYLE" ] && [ ! -s "$PREV_STYLE_FILE" ]; then
        printf '%s\n' "$current_style" > "$PREV_STYLE_FILE"
        chmod 0600 "$PREV_STYLE_FILE" 2>/dev/null
    fi

    next="$(set_style_in_json "$current" "$style")"
    settings put secure "$KEY" "$next" >/dev/null 2>&1
}

restore_style() {
    [ -s "$PREV_STYLE_FILE" ] || return 0
    previous="$(head -n 1 "$PREV_STYLE_FILE" 2>/dev/null)"
    [ -n "$previous" ] || return 0

    current="$(read_json)"
    current_style="$(extract_style "$current")"

    # Respect a later user choice: restore only if this module still owns
    # the currently-selected EXPRESSIVE style.
    if [ "$current_style" = "$TARGET_STYLE" ]; then
        next="$(set_style_in_json "$current" "$previous")"
        settings put secure "$KEY" "$next" >/dev/null 2>&1
    fi
}

case "$MODE" in
    apply)
        apply_style "$TARGET_STYLE"
        ;;
    restore)
        restore_style
        ;;
    toggle)
        current="$(read_json)"
        current_style="$(extract_style "$current")"
        if [ "$current_style" = "$TARGET_STYLE" ] && [ -s "$PREV_STYLE_FILE" ]; then
            restore_style
        else
            apply_style "$TARGET_STYLE"
        fi
        ;;
    status)
        current="$(read_json)"
        echo "theme_json=$current"
        echo "theme_style=$(extract_style "$current")"
        echo "previous_style=$(cat "$PREV_STYLE_FILE" 2>/dev/null)"
        ;;
    *)
        echo "unknown mode: $MODE" >&2
        exit 2
        ;;
esac
