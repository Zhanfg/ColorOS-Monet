#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0
# ColorOS 17 SystemUIPlugin media evidence extractor v1
# No arguments. Read-only. No reboot / force-stop / overlay or theme mutation.

set +e
umask 077

TS="$(date +%Y%m%d_%H%M%S 2>/dev/null)"
[ -n "$TS" ] || TS=unknown
BASE="/sdcard/Download"
[ -d "$BASE" ] || BASE="/storage/emulated/0/Download"
WORK="/data/local/tmp/ColorOS17_SystemUIPlugin_MediaEvidence_v1_$TS"
RAW="$WORK/raw"
OUT="$BASE/ColorOS17_SystemUIPlugin_MediaEvidence_v1_$TS.tar.gz"

mkdir -p "$RAW" || exit 1

if [ "$(id -u 2>/dev/null)" != 0 ]; then
    echo "[!] 需要 Root 权限。"
    exit 1
fi

find_apk() {
    for p in         /system_ext/app/SystemUIPlugin/SystemUIPlugin.apk         /system_ext/priv-app/SystemUIPlugin/SystemUIPlugin.apk         /product/app/SystemUIPlugin/SystemUIPlugin.apk         /product/priv-app/SystemUIPlugin/SystemUIPlugin.apk
    do
        [ -f "$p" ] && { echo "$p"; return 0; }
    done

    p="$(pm path com.oplus.systemui.plugins 2>/dev/null | sed -n 's/^package://p' | head -n 1)"
    [ -f "$p" ] && { echo "$p"; return 0; }

    find /system_ext /product /system -type f -name 'SystemUIPlugin.apk' 2>/dev/null | head -n 1
}

APK="$(find_apk)"
if [ -z "$APK" ] || [ ! -f "$APK" ]; then
    echo "[!] 未找到 SystemUIPlugin.apk"
    rm -rf "$WORK"
    exit 1
fi

echo "[*] APK: $APK"

{
    echo "time=$(date '+%F %T %z' 2>/dev/null)"
    echo "model=$(getprop ro.product.model 2>/dev/null)"
    echo "device=$(getprop ro.product.device 2>/dev/null)"
    echo "sdk=$(getprop ro.build.version.sdk 2>/dev/null)"
    echo "display=$(getprop ro.build.display.id 2>/dev/null)"
    echo "oplusrom=$(getprop ro.build.version.oplusrom 2>/dev/null)"
    echo "apk=$APK"
    ls -l "$APK" 2>/dev/null
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$APK"
    fi
} > "$WORK/baseline.txt"

unzip -Z1 "$APK" > "$WORK/zip-list.txt" 2>/dev/null

# Current PJZ110 ColorOS 17 resource-table mapping. We extract only the media
# XML blobs needed to close the static plugin layout gap.
cat > "$WORK/requested.tsv" <<'EOF'
layout/media_card_page_root	res/Jc.xml
layout/media_card_section	res/OG.xml
layout/media_immersive_bg_fullscreen	res/di.xml
layout/media_immersive_card_section	res/jK.xml
layout/media_mini_card_section	res/wN.xml
layout/media_multi_card_section	res/Dy.xml
layout/immersive_bg_page_root	res/8o.xml
layout/immersive_card_page_root	res/lV.xml
layout/mini_card_page_root	res/Ww.xml
layout/multi_page_root	res/Mq.xml
layout/normal_card_media_player_lyric_item	res/9_.xml
layout/page_bg	res/60.xml
EOF

extract_entry() {
    logical="$1"
    entry="$2"
    safe="$(printf '%s' "$logical" | tr '/ ' '__')"
    if grep -Fqx "$entry" "$WORK/zip-list.txt" 2>/dev/null; then
        unzip -p "$APK" "$entry" > "$RAW/$safe.bin" 2>/dev/null
        size="$(wc -c < "$RAW/$safe.bin" 2>/dev/null | tr -d ' ')"
        printf '%s\t%s\t%s\tOK\n' "$logical" "$entry" "$size"
    else
        printf '%s\t%s\t0\tMISSING\n' "$logical" "$entry"
    fi
}

: > "$WORK/extracted.tsv"
TAB="$(printf '\t')"
while IFS="$TAB" read -r logical entry; do
    [ -n "$logical" ] || continue
    extract_entry "$logical" "$entry" >> "$WORK/extracted.tsv"
done < "$WORK/requested.tsv"

# Include only the resource table and manifest needed to reconstruct a tiny APK
# off-device and decode the binary XML. No app/user data is collected.
for entry in AndroidManifest.xml resources.arsc; do
    if grep -Fqx "$entry" "$WORK/zip-list.txt" 2>/dev/null; then
        unzip -p "$APK" "$entry" > "$RAW/$entry" 2>/dev/null
    fi
done

{
    echo "ColorOS 17 SystemUIPlugin media evidence v1"
    echo "READ_ONLY=1"
    echo "NO_REBOOT=1"
    echo "NO_FORCE_STOP=1"
    echo "NO_THEME_MUTATION=1"
    echo "NO_OVERLAY_MUTATION=1"
    echo
    echo "Purpose:"
    echo "- decode media_card_section/root and immersive/mini/multi page topology"
    echo "- close the remaining static SystemUIPlugin resource-XML gap"
    echo "- avoid uploading the full SystemUIPlugin APK"
    echo
    echo "extracted:"
    cat "$WORK/extracted.tsv"
} > "$WORK/README.txt"

tar -czf "$OUT" -C "$(dirname "$WORK")" "$(basename "$WORK")" 2>/dev/null
RC=$?
if [ "$RC" -eq 0 ] && [ -f "$OUT" ]; then
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$OUT" > "$OUT.sha256"
    fi
    chmod 0644 "$OUT" "$OUT.sha256" 2>/dev/null
    echo "[✓] $OUT"
    rm -rf "$WORK"
    exit 0
fi

echo "[!] 打包失败，保留：$WORK"
exit 2
