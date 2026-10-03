#!/system/bin/sh
# SPDX-License-Identifier: Apache-2.0
MODDIR=${0%/*}
if [ -f "$MODDIR/bin/coloros17-expressive-style" ]; then
    /system/bin/sh "$MODDIR/bin/coloros17-expressive-style" restore >/dev/null 2>&1
fi
rm -rf /data/adb/coloros-monet
