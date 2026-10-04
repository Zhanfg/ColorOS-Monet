#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0
# ColorOS 17 MD3E narrow evidence collector v2.
# No arguments. Read-only. No reboot / force-stop / overlay or theme mutation.

set +e
umask 077

STAMP="$(date +%Y%m%d_%H%M%S 2>/dev/null)"
[ -n "$STAMP" ] || STAMP=unknown
OUTROOT=/sdcard/Download
[ -d "$OUTROOT" ] || OUTROOT=/storage/emulated/0/Download
[ -d "$OUTROOT" ] || OUTROOT="$(pwd)"

WORK="/data/local/tmp/ColorOS17_MD3E_NarrowEvidence_v2_$STAMP"
OUT="$OUTROOT/ColorOS17_MD3E_NarrowEvidence_v2_$STAMP.tar.gz"
mkdir -p "$WORK/settings_xml" "$WORK/systemui_xml" "$WORK/framework" "$WORK/runtime" || exit 1

say() { printf '%s\n' "$*"; }
have() { command -v "$1" >/dev/null 2>&1; }

[ "$(id -u 2>/dev/null)" = 0 ] || { say "[!] 需要 root。"; exit 1; }

first_apk() {
    pm path "$1" 2>/dev/null | sed -n 's/^package://p' | head -n 1
}

extract_exact() {
    apk="$1"
    entry="$2"
    destroot="$3"
    [ -f "$apk" ] || return 0
    if unzip -Z1 "$apk" 2>/dev/null | grep -Fxq "$entry"; then
        dest="$destroot/$entry"
        mkdir -p "$(dirname "$dest")"
        unzip -p "$apk" "$entry" > "$dest" 2>/dev/null
    fi
}

extract_matching_small_xml() {
    apk="$1"
    destroot="$2"
    regex="$3"
    [ -f "$apk" ] || return 0
    unzip -Z1 "$apk" 2>/dev/null | grep -E "$regex" | while IFS= read -r entry; do
        case "$entry" in *.xml) ;; *) continue ;; esac
        # Keep the evidence pack narrow.
        size="$(unzip -l "$apk" "$entry" 2>/dev/null | awk 'NR==4 {print $1}')"
        case "$size" in ''|*[!0-9]*) continue ;; esac
        [ "$size" -le 65536 ] || continue
        dest="$destroot/$entry"
        mkdir -p "$(dirname "$dest")"
        unzip -p "$apk" "$entry" > "$dest" 2>/dev/null
    done
}

SETTINGS="$(first_apk com.android.settings)"
SYSTEMUI="$(first_apk com.android.systemui)"

say "[1/6] Package provenance"
{
    echo "settings=$SETTINGS"
    echo "systemui=$SYSTEMUI"
    pm path com.android.settings 2>&1
    pm path com.android.systemui 2>&1
    pm path com.oplus.systemui.plugins 2>&1
    sha256sum "$SETTINGS" "$SYSTEMUI" 2>/dev/null
} > "$WORK/runtime/packages.txt"

say "[2/6] Settings exact grouped / Expressive XML"
for e in     res/layout/settings_homepage.xml     res/layout/settings_homepage_container.xml     res/layout/settings_homepage_container_oplus.xml     res/layout/homepage_top_category_layout.xml     res/layout/coui_preference.xml     res/layout/coui_preference_recyclerview.xml     res/layout/settingslib_expressive_preference_card.xml     res/layout-v36/settingslib_expressive_preference.xml     res/layout-v36/settingslib_expressive_preference_switch.xml     res/layout-v36/settingslib_expressive_preference_category.xml     res/layout/device_info_square_item_grid_preference.xml     res/layout/device_info_detail_preference.xml     res/layout/device_info_camera_item_layout.xml     res/layout/device_info_chip_item_layout.xml     res/xml/top_level_settings_oplus.xml     res/xml/top_level_settings_expressive.xml     res/xml/my_device_info.xml     res/xml/device_info.xml     res/drawable/card_list_item_head_bg.xml     res/drawable/card_list_item_body_bg.xml     res/drawable/card_list_item_foot_bg.xml     res/drawable/card_list_item_full_bg.xml     res/drawable/settingslib_expressive_card_background.xml     res/drawable-v36/settingslib_expressive_switch_bar_bg.xml
do
    extract_exact "$SETTINGS" "$e" "$WORK/settings_xml"
done

say "[3/6] SystemUI narrow component XML"
extract_matching_small_xml "$SYSTEMUI" "$WORK/systemui_xml" 'res/(layout|drawable|xml|color).*(qs|quick|media|volume|notification|lottie|ripple|expressive).*\.xml$'

say "[4/6] Framework ThemeStyle bytecode source"
FRAMEWORK=/system/framework/framework.jar
if [ -f "$FRAMEWORK" ]; then
    unzip -Z1 "$FRAMEWORK" 2>/dev/null | grep -E '^classes([0-9]+)?\.dex$' > "$WORK/framework/framework_dex_list.txt"
    while IFS= read -r dex; do
        [ -n "$dex" ] || continue
        unzip -p "$FRAMEWORK" "$dex" > "$WORK/framework/$dex" 2>/dev/null
    done < "$WORK/framework/framework_dex_list.txt"
    sha256sum "$FRAMEWORK" > "$WORK/framework/framework_jar.sha256" 2>/dev/null
else
    echo "framework.jar missing" > "$WORK/framework/README.txt"
fi

say "[5/6] Runtime ownership snapshot"
{
    echo "time=$(date '+%F %T %z' 2>/dev/null)"
    echo "theme_json=$(settings get secure theme_customization_overlay_packages 2>/dev/null)"
    echo "--- activity ---"
    dumpsys activity activities 2>/dev/null | grep -E 'mResumedActivity|topResumedActivity|mFocusedApp' | head -n 100
    echo "--- window ---"
    dumpsys window windows 2>/dev/null | grep -E 'mCurrentFocus|mFocusedApp' | head -n 100
    echo "--- relevant logs ---"
    logcat -b all -d -v threadtime 2>/dev/null | grep -Ei 'NoSuchFieldError|mCardBackgroundColor|COUICardListSelectedItemLayout|COUICustomListSelectedLinearLayout|QSIconViewProxy|OplusVolumeDialogImpl|VolumeMaterialCapability|VolumePlatformBlurSession|MediaPlayerCardPageRootView' | tail -n 8000
} > "$WORK/runtime/runtime.txt"

say "[6/6] Manifest + package"
{
    echo "collector=ColorOS17_MD3E_NarrowEvidence_v2"
    echo "read_only=1"
    echo "no_reboot=1"
    echo "no_force_stop=1"
    echo "no_theme_mutation=1"
    echo "no_overlay_mutation=1"
    echo "purpose=close Codex XML/framework/runtime gates"
} > "$WORK/README.txt"

find "$WORK" -type f -print0 2>/dev/null | sort -z | xargs -0 sha256sum > "$WORK/SHA256SUMS" 2>/dev/null
tar -czf "$OUT" -C "$WORK" . 2>/dev/null || {
    say "[!] 打包失败，保留：$WORK"
    exit 2
}
sha256sum "$OUT" > "$OUT.sha256" 2>/dev/null
chmod 0644 "$OUT" "$OUT.sha256" 2>/dev/null

# Auto-split if upload size is likely inconvenient.
SIZE="$(wc -c < "$OUT" 2>/dev/null | tr -d ' ')"
case "$SIZE" in ''|*[!0-9]*) SIZE=0 ;; esac
if [ "$SIZE" -gt 8388608 ]; then
    PARTDIR="$OUT.parts"
    mkdir -p "$PARTDIR"
    split -b 8m -d -a 3 "$OUT" "$PARTDIR/$(basename "$OUT").part-" 2>/dev/null
    if [ $? -eq 0 ]; then
        {
            echo "source=$(basename "$OUT")"
            echo "source_size=$SIZE"
            echo "source_sha256=$(sha256sum "$OUT" 2>/dev/null | awk '{print $1}')"
            echo "reassemble=cat $(basename "$OUT").part-* > $(basename "$OUT")"
            for f in "$PARTDIR"/*.part-*; do
                [ -f "$f" ] || continue
                sha256sum "$f"
            done
        } > "$PARTDIR/SPLIT_MANIFEST.txt"
        chmod 0644 "$PARTDIR"/* 2>/dev/null
        say "[✓] 分卷目录：$PARTDIR"
    fi
fi

say "[✓] $OUT"
rm -rf "$WORK"
