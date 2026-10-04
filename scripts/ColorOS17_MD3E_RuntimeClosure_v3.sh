#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0
# One-shot ColorOS 17 MD3E runtime closure. No args, no reboot.
# Temporarily restarts Settings for native Expressive A/B and restores the original property.

set +e
umask 077
P=is_expressive_design_enabled
T="$(date +%Y%m%d_%H%M%S 2>/dev/null)"
D=/sdcard/Download
[ -d "$D" ] || D=/storage/emulated/0/Download
W="/data/local/tmp/COS17_MD3E_RuntimeClosure_$T"
O="$D/ColorOS17_MD3E_RuntimeClosure_v3_$T.tar.gz"
mkdir -p "$W"/{base,A_off,B_on,restored,xml/settings,xml/media,runtime,logs} || exit 1
[ "$(id -u)" = 0 ] || { echo "[!] root required"; exit 1; }

have(){ command -v "$1" >/dev/null 2>&1; }
apk(){ pm path "$1" 2>/dev/null | sed -n 's/^package://p' | head -n1; }
hash(){ [ -f "$1" ] && sha256sum "$1" 2>/dev/null; }
rp=""
for x in "$(command -v resetprop 2>/dev/null)" /data/adb/ksu/bin/resetprop /data/adb/magisk/resetprop; do
  [ -n "$x" ] && [ -x "$x" ] && { rp="$x"; break; }
done
orig="$(getprop "$P")"
getprop | grep -Fq "[$P]:" && present=1 || present=0

putp(){ [ -n "$rp" ] && "$rp" "$P" "$1" >/dev/null 2>&1 || setprop "$P" "$1"; }
restore(){
  if [ "$present" = 0 ] && [ -n "$rp" ]; then "$rp" -d "$P" >/dev/null 2>&1 || "$rp" "$P" ""; else putp "$orig"; fi
}
restart_settings(){ am force-stop com.android.settings >/dev/null 2>&1; sleep 1; am start -W -a android.settings.SETTINGS >/dev/null 2>&1; sleep 3; }
trap 'restore; restart_settings' 1 2 15

S="$(apk com.android.settings)"
U="$(apk com.android.systemui)"
M="$(apk com.oplus.systemui.plugins)"
X="$(apk com.oplus.uxdesign)"
C="$(apk one.dot.couiexpressive)"

{
 echo "time=$(date '+%F %T %z')"
 echo "model=$(getprop ro.product.model)"
 echo "sdk=$(getprop ro.build.version.sdk)"
 echo "display=$(getprop ro.build.display.id)"
 echo "fingerprint=$(getprop ro.build.fingerprint)"
 echo "settings=$S"; echo "systemui=$U"; echo "plugin=$M"; echo "uxdesign=$X"; echo "coe=$C"
 echo "orig_expressive=$orig"; echo "orig_present=$present"; echo "resetprop=${rp:-none}"
 echo "theme_json=$(settings get secure theme_customization_overlay_packages 2>/dev/null)"
 echo "material_blur=$(getprop persist.sys.oplus.material_blur_switch)"
} > "$W/base/device.txt"
for f in "$S" "$U" "$M" "$X" "$C"; do hash "$f"; done > "$W/base/apk_sha256.txt"
cmd overlay list --user 0 > "$W/runtime/overlay_list.txt" 2>&1

extract(){
  a="$1"; e="$2"; d="$3"
  [ -f "$a" ] || return
  unzip -Z1 "$a" 2>/dev/null | grep -Fxq "$e" || return
  mkdir -p "$d/$(dirname "$e")"
  unzip -p "$a" "$e" > "$d/$e" 2>/dev/null
}
for e in \
 res/xml/top_level_settings_oplus.xml \
 res/xml/top_level_settings_expressive.xml \
 res/layout/settingslib_expressive_preference_card.xml \
 res/layout-v36/settingslib_expressive_preference.xml \
 res/layout-v36/settingslib_expressive_preference_switch.xml \
 res/drawable/card_list_item_head_bg.xml \
 res/drawable/card_list_item_body_bg.xml \
 res/drawable/card_list_item_foot_bg.xml \
 res/drawable/card_list_item_full_bg.xml \
 res/drawable/settingslib_expressive_card_background.xml
do extract "$S" "$e" "$W/xml/settings"; done

if [ -f "$M" ]; then
  for e in res/Jc.xml res/OG.xml res/di.xml res/jK.xml res/wN.xml res/Dy.xml res/8o.xml res/lV.xml res/Ww.xml res/Mq.xml res/9_.xml res/60.xml; do
    extract "$M" "$e" "$W/xml/media"
  done
  unzip -p "$M" resources.arsc > "$W/xml/media/resources.arsc" 2>/dev/null
  unzip -p "$M" AndroidManifest.xml > "$W/xml/media/AndroidManifest.xml" 2>/dev/null
fi

cap(){
  q="$1"; tag="$2"
  {
    echo "tag=$tag"; echo "prop=$(getprop "$P")"
    dumpsys activity activities 2>/dev/null | grep -E 'mResumedActivity|topResumedActivity|OplusSettingsHomepageActivity|OplusTopLevelSettings' | head -n200
  } > "$q/state.txt"
  screencap -p "$q/screen.png" >/dev/null 2>&1
  if have uiautomator; then
    uiautomator dump "$q/raw.xml" >/dev/null 2>&1
    sed -E 's/text="[^"]*"/text=""/g;s/content-desc="[^"]*"/content-desc=""/g;s/hint="[^"]*"/hint=""/g' "$q/raw.xml" > "$q/window.xml"
    rm -f "$q/raw.xml"
  fi
}

ab=skipped
if [ -n "$rp" ]; then
  putp false; restart_settings; cap "$W/A_off" A_OFF
  putp true; restart_settings; cap "$W/B_on" B_ON
  restore; restart_settings; cap "$W/restored" RESTORED
  ab=completed
fi
{
 echo "ab=$ab"
 if [ "$ab" = completed ]; then
   cmp -s "$W/A_off/window.xml" "$W/B_on/window.xml" && echo "uia_changed=0" || echo "uia_changed=1"
   a="$(hash "$W/A_off/screen.png" | awk '{print $1}')"; b="$(hash "$W/B_on/screen.png" | awk '{print $1}')"
   echo "screen_a=$a"; echo "screen_b=$b"; [ -n "$a" ] && [ "$a" = "$b" ] && echo "pixels_changed=0" || echo "pixels_changed=1"
 fi
} > "$W/runtime/ab_summary.txt"

{
 dumpsys window windows 2>/dev/null | grep -E 'mCurrentFocus|mFocusedApp|Settings|SystemUI|Volume|Media|QuickSettings' | head -n500
 echo "--- layers ---"
 dumpsys SurfaceFlinger --list 2>/dev/null | grep -Ei 'notification|shade|quick|qs|volume|media|keyguard|settings' | head -n1000
} > "$W/runtime/components.txt"
logcat -b all -d -v threadtime 2>/dev/null | grep -Ei -B15 -A40 \
 'NoSuchFieldError|mCardBackgroundColor|CardHook|ListHook|QSIconViewProxy|SimpleQsClock|OplusVolumeDialogImpl|VolumeMaterialCapability|MediaPlayerCardPageRootView|one\.dot\.couiexpressive' | tail -n12000 > "$W/logs/targeted.txt"

{
 echo "collector=RuntimeClosure_v3"; echo "ab=$ab"; echo "reboot=0"; echo "systemui_restart=0"
 echo "theme_mutation=0"; echo "overlay_mutation=0"; echo "restored_prop=$(getprop "$P")"
 echo "screenshots=Settings homepage A/B only"
 echo "uia_text_sanitized=1"
} > "$W/README.txt"
find "$W" -type f -print0 | sort -z | xargs -0 sha256sum > "$W/SHA256SUMS" 2>/dev/null

tar -czf "$O" -C "$W" . || exit 2
sha256sum "$O" > "$O.sha256"
restore
trap - 1 2 15
restart_settings

size="$(wc -c < "$O" | tr -d ' ')"
if [ "$size" -gt 8388608 ]; then
  PDIR="$O.parts"; rm -rf "$PDIR"; mkdir -p "$PDIR"
  split -b 8m -d -a3 "$O" "$PDIR/$(basename "$O").part-" 2>/dev/null
  { echo "source=$(basename "$O")"; sha256sum "$O"; echo "reassemble=cat $(basename "$O").part-* > $(basename "$O")"; } > "$PDIR/SPLIT_MANIFEST.txt"
fi
rm -rf "$W"
echo "[✓] $O"
echo "[✓] Expressive property restored: '$(getprop "$P")'"
