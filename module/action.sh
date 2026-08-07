#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0

MODDIR="${0%/*}"
BASE=/data/adb/coloros-monet
RUNTIME="$BASE/runtime"
FRONTEND_APK="$MODDIR/frontend/COE-2.5.apk"
FRONTEND_PACKAGE="one.dot.couiexpressive"
FRONTEND_ACTIVITY="one.dot.couiexpressive.ui.SettingsActivity"
FRONTEND_ALIAS="one.dot.couiexpressive.LauncherActivityAlias"

mkdir -p "$RUNTIME"

echo "[ColorOS Monet] Opening COE frontend"

if ! pm path "$FRONTEND_PACKAGE" >/dev/null 2>&1 && [ -f "$FRONTEND_APK" ]; then
  echo "- Frontend not installed; installing bundled COE"
  pm install -r --user 0 "$FRONTEND_APK" >"$RUNTIME/frontend-action-install.log" 2>&1 || true
fi

if pm path "$FRONTEND_PACKAGE" >/dev/null 2>&1; then
  if am start --user 0 -n "$FRONTEND_PACKAGE/$FRONTEND_ALIAS" >/dev/null 2>&1; then
    echo "- COE frontend opened through launcher alias"
    exit 0
  fi
  if am start --user 0 -n "$FRONTEND_PACKAGE/$FRONTEND_ACTIVITY" >/dev/null 2>&1; then
    echo "- COE frontend opened through SettingsActivity"
    exit 0
  fi
  if command -v monkey >/dev/null 2>&1 && monkey -p "$FRONTEND_PACKAGE" -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1; then
    echo "- COE frontend opened through launcher intent"
    exit 0
  fi
  echo "! COE is installed but Android refused to launch its settings activity"
  exit 1
fi

echo "! COE frontend is not installed and no installable frontend was found"
exit 1
