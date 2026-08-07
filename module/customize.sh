#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0

# Read by Magisk / KernelSU / APatch installer framework.
# shellcheck disable=SC2034
SKIPMOUNT=true

FRONTEND_REL="frontend/COE-2.5.apk"
FRONTEND_APK="$MODPATH/$FRONTEND_REL"
FRONTEND_HASH_FILE="$MODPATH/frontend/COE-2.5.apk.sha256"

ui_print "********************************"
ui_print " ColorOS Monet + COE Frontend"
ui_print " Rust / CMONET01 + COE frontend"
ui_print "********************************"

ARCH_NOW="${ARCH:-$(getprop ro.product.cpu.abi 2>/dev/null)}"
case "$ARCH_NOW" in
  arm64|arm64-v8a|aarch64) ;;
  *) abort "Unsupported architecture: $ARCH_NOW (arm64 required)" ;;
esac

SDK_NOW="${API:-$(getprop ro.build.version.sdk 2>/dev/null)}"
case "$SDK_NOW" in
  ''|*[!0-9]*) abort "Unable to determine Android SDK" ;;
esac
[ "$SDK_NOW" -ge 31 ] || abort "Android 12 / SDK 31 or newer is required"

[ -x "$MODPATH/bin/monetctl" ] || chmod 0755 "$MODPATH/bin/monetctl" 2>/dev/null
[ -x "$MODPATH/bin/monetctl" ] || abort "monetctl runtime is missing or not executable"

# APKs remain forbidden except for the one explicitly designated user-facing
# COE frontend. The public repository does not contain that binary; local/private
# builds may inject it with tools/package_module.py --frontend-apk.
APK_COUNT=0
BAD_APK=0
for APK in $(find "$MODPATH" -type f -name '*.apk' 2>/dev/null); do
  APK_COUNT=$((APK_COUNT + 1))
  [ "$APK" = "$FRONTEND_APK" ] || {
    ui_print "! Unexpected APK payload: ${APK#$MODPATH/}"
    BAD_APK=1
  }
done
[ "$BAD_APK" = "0" ] || abort "Unexpected APK payload detected"
[ "$APK_COUNT" -le 1 ] || abort "Only the COE frontend APK may be bundled"

if [ -f "$FRONTEND_APK" ]; then
  if command -v sha256sum >/dev/null 2>&1 && [ -f "$FRONTEND_HASH_FILE" ]; then
    EXPECTED_HASH="$(awk 'NR==1{print $1}' "$FRONTEND_HASH_FILE" 2>/dev/null)"
    ACTUAL_HASH="$(sha256sum "$FRONTEND_APK" 2>/dev/null | awk '{print $1}')"
    [ -n "$EXPECTED_HASH" ] && [ "$EXPECTED_HASH" = "$ACTUAL_HASH" ] || abort "COE frontend APK hash mismatch"
  fi
  ui_print "- COE frontend bundled"
else
  ui_print "- COE frontend not bundled; backend-only install"
fi

COMPONENT_COUNT="$(find "$MODPATH/components" -maxdepth 1 -type f -name '*.cmonet' 2>/dev/null | wc -l | tr -d ' ')"
[ "$COMPONENT_COUNT" -ge 40 ] || abort "Expected at least 40 CMONET01 components, found $COMPONENT_COUNT"

ui_print "- Verifying $COMPONENT_COUNT component package headers"
VERIFY_FAILED=0
for PACKAGE in "$MODPATH"/components/*.cmonet; do
  [ -f "$PACKAGE" ] || continue
  "$MODPATH/bin/monetctl" verify "$PACKAGE" >/dev/null 2>&1 || {
    ui_print "! Invalid component: $(basename "$PACKAGE")"
    VERIFY_FAILED=1
  }
done
[ "$VERIFY_FAILED" = "0" ] || abort "Component verification failed"

mkdir -p /data/adb/coloros-monet 2>/dev/null
cat > /data/adb/coloros-monet/install-info.txt <<INFO
version=@VERSION@
versionCode=@VERSION_CODE@
sdk=$SDK_NOW
arch=$ARCH_NOW
components=$COMPONENT_COUNT
backend=fabricated-overlay
frontend=one.dot.couiexpressive
frontend_bundled=$([ -f "$FRONTEND_APK" ] && echo true || echo false)
package_magic=CMONET01
INFO

set_perm_recursive "$MODPATH" 0 0 0755 0644
set_perm "$MODPATH/bin/monetctl" 0 0 0755
set_perm "$MODPATH/customize.sh" 0 0 0755
set_perm "$MODPATH/post-fs-data.sh" 0 0 0755
set_perm "$MODPATH/service.sh" 0 0 0755
set_perm "$MODPATH/action.sh" 0 0 0755
set_perm "$MODPATH/uninstall.sh" 0 0 0755

ui_print "- SKIPMOUNT=true; frontend is installed through Package Manager after boot"
ui_print "- Module Action opens the COE frontend"
ui_print "- LSPosed scope is never enabled automatically"
