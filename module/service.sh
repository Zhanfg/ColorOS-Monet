#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0

MODDIR="${0%/*}"
BASE=/data/adb/coloros-monet
STORE="$BASE/components"
RUNTIME="$BASE/runtime"
LOG="$BASE/service.log"
PIDFILE="$RUNTIME/watcher.pid"
DISABLED="$BASE/global-disabled"

mkdir -p "$STORE" "$RUNTIME"

wait_for_boot() {
  COUNT=0
  while [ "$(getprop sys.boot_completed 2>/dev/null)" != "1" ] && [ "$COUNT" -lt 180 ]; do
    sleep 2
    COUNT=$((COUNT + 1))
  done
}

stop_old_watcher() {
  [ -f "$PIDFILE" ] || return 0
  PID="$(cat "$PIDFILE" 2>/dev/null)"
  case "$PID" in ''|*[!0-9]*) rm -f "$PIDFILE"; return 0 ;; esac
  if kill -0 "$PID" 2>/dev/null; then
    kill "$PID" 2>/dev/null
    sleep 1
  fi
  rm -f "$PIDFILE"
}

{
  echo "[$(date '+%F %T %z' 2>/dev/null)] service start"
  wait_for_boot
  "$MODDIR/bin/monetctl" sync "$MODDIR/components" --store "$STORE" --enable-defaults
  if [ -f "$DISABLED" ]; then
    echo "global state is disabled; components remain installed"
    "$MODDIR/bin/monetctl" disable-all --store "$STORE" || true
    exit 0
  fi
  "$MODDIR/bin/monetctl" apply-all --store "$STORE" || true
  stop_old_watcher
  "$MODDIR/bin/monetctl" watch --store "$STORE" --runtime-dir "$RUNTIME" --interval-seconds 20 >>"$BASE/watcher.log" 2>&1 &
  echo "$!" >"$PIDFILE"
  echo "watcher pid=$!"
} >>"$LOG" 2>&1
