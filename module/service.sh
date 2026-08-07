#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0

MODDIR="${0%/*}"
BASE=/data/adb/coloros-monet
STORE="$BASE/components"
RUNTIME="$BASE/runtime"
LOG="$BASE/service.log"
PIDFILE="$RUNTIME/watcher.pid"
DISABLED="$BASE/global-disabled"
FRONTEND_APK="$MODDIR/frontend/COE-2.5.apk"
FRONTEND_PACKAGE="one.dot.couiexpressive"
FRONTEND_MARKER="$BASE/frontend-installed-by-module"
FRONTEND_STATUS="$BASE/frontend.status"

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

install_frontend() {
  if [ ! -f "$FRONTEND_APK" ]; then
    echo "bundled=false" > "$FRONTEND_STATUS"
    echo "state=not-bundled" >> "$FRONTEND_STATUS"
    return 0
  fi

  PREEXISTING=false
  pm path "$FRONTEND_PACKAGE" >/dev/null 2>&1 && PREEXISTING=true

  INSTALL_LOG="$RUNTIME/frontend-install.log"
  if pm install -r --user 0 "$FRONTEND_APK" >"$INSTALL_LOG" 2>&1; then
    echo "bundled=true" > "$FRONTEND_STATUS"
    echo "state=installed" >> "$FRONTEND_STATUS"
    echo "package=$FRONTEND_PACKAGE" >> "$FRONTEND_STATUS"
    [ "$PREEXISTING" = false ] && touch "$FRONTEND_MARKER"
    echo "COE frontend install/update accepted by Package Manager"
  elif pm path "$FRONTEND_PACKAGE" >/dev/null 2>&1; then
    echo "bundled=true" > "$FRONTEND_STATUS"
    echo "state=existing-kept" >> "$FRONTEND_STATUS"
    echo "package=$FRONTEND_PACKAGE" >> "$FRONTEND_STATUS"
    echo "COE frontend already exists; bundled update was rejected, existing package kept"
    cat "$INSTALL_LOG" 2>/dev/null || true
  else
    echo "bundled=true" > "$FRONTEND_STATUS"
    echo "state=install-failed" >> "$FRONTEND_STATUS"
    echo "package=$FRONTEND_PACKAGE" >> "$FRONTEND_STATUS"
    echo "COE frontend installation failed; backend continues"
    cat "$INSTALL_LOG" 2>/dev/null || true
  fi
}

{
  echo "[$(date '+%F %T %z' 2>/dev/null)] service start"
  wait_for_boot
  install_frontend
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
