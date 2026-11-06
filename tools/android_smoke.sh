#!/usr/bin/env bash
# Only run against a privately built Gothic debug APK; do not upload game data.
set -euo pipefail
if [ "$#" -ne 1 ] || [ ! -f "$1" ]; then
  echo 'Usage: bash tools/android_smoke.sh /path/to/private/Gothic3-debug.apk' >&2
  exit 2
fi
APK=$(realpath "$1")
PKG="org.gothic3.fanport.debug"
ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUT="$ROOT/.work/android-smoke-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUT"
if ! command -v adb >/dev/null 2>&1; then
  echo 'adb is not installed' >&2
  exit 1
fi
if [ "$(adb devices | awk '$2 == "device" {count++} END {print count+0}')" -ne 1 ]; then
  echo 'Connect and authorize exactly one Android device through adb' >&2
  exit 1
fi
adb install -r "$APK" | tee "$OUT/install.txt"
adb shell monkey -p "$PKG" -c android.intent.category.LAUNCHER 1 | tee "$OUT/launch.txt"
echo 'Verify game view, then press Enter to capture screenshot and logcat.'
read -r _
adb exec-out screencap -p > "$OUT/screenshot.png"
adb logcat -d -v time > "$OUT/logcat.txt"
echo "Captured: $OUT"
echo 'Verify movement, atlas 005, transitions, audio, RMS save, restart manually.'
echo 'Review screenshots/logcat before sharing: they may contain personal information.'
