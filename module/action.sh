#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0

MODDIR="${0%/*}"
BASE=/data/adb/coloros-monet
STORE="$BASE/components"
RUNTIME="$BASE/runtime"
PIDFILE="$RUNTIME/watcher.pid"
DISABLED="$BASE/global-disabled"

stop_watcher() {
  [ -f "$PIDFILE" ] || return 0
  PID="$(cat "$PIDFILE" 2>/dev/null)"
  case "$PID" in ''|*[!0-9]*) rm -f "$PIDFILE"; return 0 ;; esac
  kill "$PID" 2>/dev/null || true
  rm -f "$PIDFILE"
}

mkdir -p "$STORE" "$RUNTIME"
"$MODDIR/bin/monetctl" sync "$MODDIR/components" --store "$STORE" --enable-defaults || exit 1

if [ -f "$DISABLED" ]; then
  echo "[ColorOS Monet] Enabling default components"
  rm -f "$DISABLED"
  "$MODDIR/bin/monetctl" apply-all --store "$STORE" || true
  stop_watcher
  "$MODDIR/bin/monetctl" watch --store "$STORE" --runtime-dir "$RUNTIME" --interval-seconds 20 >>"$BASE/watcher.log" 2>&1 &
  echo "$!" >"$PIDFILE"
else
  echo "[ColorOS Monet] Disabling all components"
  touch "$DISABLED"
  stop_watcher
  "$MODDIR/bin/monetctl" disable-all --store "$STORE" || true
fi

echo
echo "Component state:"
"$MODDIR/bin/monetctl" list --store "$STORE" 2>/dev/null || true
