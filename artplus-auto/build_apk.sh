#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
APP="$ROOT/app"
OUT="$ROOT/dist"
WORK="$ROOT/.standalone-build"

ANDROID_HOME="${ANDROID_HOME:-/usr/local/lib/android/sdk}"
ANDROID_JAR="$ANDROID_HOME/platforms/android-35/android.jar"
BUILD_TOOLS="$ANDROID_HOME/build-tools/35.0.0"
AAPT2="$BUILD_TOOLS/aapt2"
D8="$BUILD_TOOLS/d8"
ZIPALIGN="$BUILD_TOOLS/zipalign"
APKSIGNER="$BUILD_TOOLS/apksigner"

for tool in "$AAPT2" "$D8" "$ZIPALIGN" "$APKSIGNER"; do
    [ -x "$tool" ] || { echo "missing Android build tool: $tool" >&2; exit 2; }
done
[ -f "$ANDROID_JAR" ] || { echo "missing android.jar: $ANDROID_JAR" >&2; exit 2; }

KOTLINC="${KOTLINC:-$(command -v kotlinc || true)}"
[ -n "$KOTLINC" ] && [ -x "$KOTLINC" ] || {
    echo "kotlinc not found" >&2
    exit 2
}

rm -rf "$WORK" "$OUT"
mkdir -p "$WORK/dex" "$OUT"

mapfile -d '' SOURCES < <(find "$APP/src/main/java" -type f -name '*.kt' -print0 | sort -z)
[ "${#SOURCES[@]}" -gt 0 ] || { echo "no Kotlin sources found" >&2; exit 2; }

echo "[1/6] Kotlin compile"
"$KOTLINC"     -jvm-target 17     -classpath "$ANDROID_JAR"     -include-runtime     -d "$WORK/app-classes.jar"     "${SOURCES[@]}"

echo "[2/6] DEX"
"$D8"     --min-api 33     --lib "$ANDROID_JAR"     --output "$WORK/dex"     "$WORK/app-classes.jar"

echo "[3/6] Android resources"
"$AAPT2" compile     --dir "$APP/src/main/res"     -o "$WORK/resources.zip"

"$AAPT2" link     -I "$ANDROID_JAR"     --manifest "$APP/src/main/AndroidManifest.xml"     --min-sdk-version 33     --target-sdk-version 35     --version-code 1     --version-name 0.1.0-alpha1     -o "$WORK/unsigned-unaligned.apk"     "$WORK/resources.zip"

(
    cd "$WORK/dex"
    zip -q -u "$WORK/unsigned-unaligned.apk" classes.dex
)

echo "[4/6] Align"
"$ZIPALIGN" -f 4 "$WORK/unsigned-unaligned.apk" "$WORK/aligned.apk"

echo "[5/6] Debug sign"
KEYSTORE="$WORK/debug.jks"
keytool -genkeypair     -keystore "$KEYSTORE"     -storepass android     -alias androiddebugkey     -keypass android     -dname "CN=Android Debug,O=Android,C=US"     -keyalg RSA     -keysize 2048     -validity 10000     >/dev/null 2>&1

APK="$OUT/ColorOS17-ARTPlus-Auto-0.1.0-alpha1.apk"
"$APKSIGNER" sign     --ks "$KEYSTORE"     --ks-key-alias androiddebugkey     --ks-pass pass:android     --key-pass pass:android     --out "$APK"     "$WORK/aligned.apk"

echo "[6/6] Verify"
"$APKSIGNER" verify --verbose "$APK"
"$AAPT2" dump badging "$APK" | head -n 8
sha256sum "$APK" | tee "$OUT/SHA256SUMS.txt"
echo "built: $APK"
