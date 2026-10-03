#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0
# Read-only post-boot audit for ColorOS 17 native-first + MD3E.
# No arguments, no app/service restart, no overlay mutation.

STAMP="$(date +%Y%m%d_%H%M%S 2>/dev/null)"
[ -n "$STAMP" ] || STAMP=unknown
OUT="/sdcard/Download/ColorOS17_MD3E_PostBootAudit_v1_$STAMP.txt"
MOD="/data/adb/modules/material_you_for_coloros"

have() { command -v "$1" >/dev/null 2>&1; }

{
    echo "============================================================"
    echo " ColorOS 17 × MD3E Post-Boot Audit v1"
    echo " READ ONLY / NO RESTART / NO OVERLAY CHANGES"
    echo "============================================================"
    echo "time=$(date '+%F %T %z' 2>/dev/null)"
    echo "model=$(getprop ro.product.model 2>/dev/null)"
    echo "device=$(getprop ro.product.device 2>/dev/null)"
    echo "android=$(getprop ro.build.version.release 2>/dev/null)"
    echo "sdk=$(getprop ro.build.version.sdk 2>/dev/null)"
    echo "display=$(getprop ro.build.display.id 2>/dev/null)"
    echo "oplusrom=$(getprop ro.build.version.oplusrom 2>/dev/null)"
    echo

    echo "--- theme / ColorOS native Monet ---"
    THEME="$(settings get secure theme_customization_overlay_packages 2>/dev/null)"
    echo "theme_customization_overlay_packages=$THEME"
    echo "theme_style=$(printf '%s' "$THEME" | sed -n 's/.*"android.theme.customization.theme_style":"\([^"]*\)".*/\1/p')"
    echo "material_blur=$(getprop persist.sys.oplus.material_blur_switch 2>/dev/null)"
    echo "sf_media_panel_blur=$(getprop ro.surface_flinger.media_panel_bg_blur 2>/dev/null)"
    echo "sf_background_blur=$(getprop ro.surface_flinger.supports_background_blur 2>/dev/null)"
    echo

    echo "--- module ---"
    if [ -f "$MOD/module.prop" ]; then
        cat "$MOD/module.prop"
    else
        echo "module_missing=$MOD"
    fi
    echo

    echo "--- mounted overlay files ---"
    find "$MOD/system/product/overlay" -maxdepth 1 -type f \( -name '*.apk' -o -name '*.apk.disabled' \) 2>/dev/null | sort
    echo

    echo "--- PackageManager recognition ---"
    for pkg in \
        dev.zhanfg.colorosmonet.native.settings \
        dev.zhanfg.colorosmonet.native.systemui \
        dev.zhanfg.colorosmonet.native.launcher \
        dev.zhanfg.colorosmonet.native.wirelesssettings \
        dev.zhanfg.colorosmonet.native.notificationmanager \
        dev.zhanfg.coloros17.exact.settings.extra \
        com.android.settings.overlay \
        com.android.systemui.overlay \
        com.android.launcher.overlay \
        one.dot.couiexpressive
    do
        echo "===== $pkg ====="
        pm path "$pkg" 2>&1
        dumpsys package "$pkg" 2>/dev/null | grep -E 'versionName=|versionCode=' | head -n 4
    done
    echo

    echo "--- OverlayManager ---"
    if have timeout; then
        timeout 6 cmd overlay list --user 0 2>&1 | grep -E 'zhanfg|settings\.overlay|systemui\.overlay|launcher\.overlay' || true
    else
        cmd overlay list --user 0 2>&1 | grep -E 'zhanfg|settings\.overlay|systemui\.overlay|launcher\.overlay' || true
    fi
    echo

    echo "--- effective resource lookups ---"
    for spec in \
        'com.android.settings com.android.settings:dimen/coui_round_corner_m' \
        'com.android.settings com.android.settings:color/coui_color_divider' \
        'com.android.settings com.android.settings:color/coui_color_card_background' \
        'com.android.systemui com.android.systemui:dimen/notification_corner_radius' \
        'com.android.systemui com.android.systemui:dimen/volume_vertical_row_radius' \
        'com.android.systemui com.android.systemui:integer/blur_radius_platform_config' \
        'com.android.systemui com.android.systemui:color/qs_hl_tile_indicator_inactive_bg_color' \
        'com.android.launcher com.android.launcher:dimen/coui_round_corner_s' \
        'com.android.launcher com.android.launcher:dimen/widget_popup_group_divider_height' \
        'com.oplus.wirelesssettings com.oplus.wirelesssettings:dimen/coui_list_divider_height'
    do
        target="$(printf '%s' "$spec" | cut -d' ' -f1)"
        res="$(printf '%s' "$spec" | cut -d' ' -f2)"
        echo "===== $res ====="
        if have timeout; then
            timeout 5 cmd overlay lookup --verbose "$target" "$res" 2>&1
        else
            cmd overlay lookup --verbose "$target" "$res" 2>&1
        fi
    done
    echo

    echo "--- idmap cache for module overlays ---"
    find /data/resource-cache -type f 2>/dev/null | grep -Ei 'zhanfg|settings@idmap|systemui@idmap|launcher@idmap' | sort | head -n 500
    echo

    echo "--- recent COE / card / resource errors ---"
    logcat -b all -d -v threadtime 2>/dev/null | grep -Ei \
        'one\.dot\.couiexpressive|CardHook|ListHook|COUICustomListSelectedLinearLayout|COUICardListSelectedItemLayout|NoSuchFieldError|Resources\$NotFoundException|FATAL EXCEPTION' | tail -n 5000
    echo

    echo "--- verdict hints ---"
    style="$(printf '%s' "$THEME" | sed -n 's/.*"android.theme.customization.theme_style":"\([^"]*\)".*/\1/p')"
    [ "$style" = EXPRESSIVE ] && echo "theme_style_ok=1" || echo "theme_style_ok=0 current=$style"
    [ "$(getprop persist.sys.oplus.material_blur_switch 2>/dev/null)" = true ] && echo "material_blur_ok=1" || echo "material_blur_ok=0"
    echo "note=OverlayManager lookup failure alone is not treated as a failed module; inspect pm/idmap evidence too."
} > "$OUT" 2>&1

chmod 0644 "$OUT" 2>/dev/null
echo "[✓] $OUT"
