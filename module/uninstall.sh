#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0

MODDIR="${0%/*}"
BASE=/data/adb/coloros-monet
STORE="$BASE/components"
PIDFILE="$BASE/runtime/watcher.pid"

if [ -f "$PIDFILE" ]; then
  PID="$(cat "$PIDFILE" 2>/dev/null)"
  case "$PID" in ''|*[!0-9]*) ;; *) kill "$PID" 2>/dev/null || true ;; esac
fi

[ -x "$MODDIR/bin/monetctl" ] && "$MODDIR/bin/monetctl" disable-all --store "$STORE" >/dev/null 2>&1 || true
rm -rf "$BASE"
