#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0

SKIPMOUNT=true

ui_print "*******************************"
ui_print " ColorOS Monet Component Runtime"
ui_print " Rust + CMONET01 packages"
ui_print "*******************************"

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

APK_COUNT="$(find "$MODPATH" -type f -name '*.apk' 2>/dev/null | wc -l | tr -d ' ')"
[ "$APK_COUNT" = "0" ] || abort "APK payloads are forbidden in runtime v2"

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
package_magic=CMONET01
INFO

set_perm_recursive "$MODPATH" 0 0 0755 0644
set_perm "$MODPATH/bin/monetctl" 0 0 0755
set_perm "$MODPATH/customize.sh" 0 0 0755
set_perm "$MODPATH/post-fs-data.sh" 0 0 0755
set_perm "$MODPATH/service.sh" 0 0 0755
set_perm "$MODPATH/action.sh" 0 0 0755
set_perm "$MODPATH/uninstall.sh" 0 0 0755

ui_print "- APK-free module base enabled (SKIPMOUNT=true)"
ui_print "- Components will be synchronized after reboot"
ui_print "- Device overlay policy may reject individual targets; inspect runtime logs"
