#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0

MODDIR="${0%/*}"
BASE=/data/adb/coloros-monet
STORE="$BASE/components"
RUNTIME="$BASE/runtime"
LOG="$BASE/post-fs-data.log"

mkdir -p "$STORE" "$RUNTIME"
chmod 0700 "$BASE" "$STORE" "$RUNTIME" 2>/dev/null

{
  echo "[$(date '+%F %T %z' 2>/dev/null)] post-fs-data sync"
  "$MODDIR/bin/monetctl" sync "$MODDIR/components" --store "$STORE"
} >>"$LOG" 2>&1
