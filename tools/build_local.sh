#!/usr/bin/env bash
# Build the Gothic Android app from this checkout. Optional private replacement JAR.
set -euo pipefail
if [[ "$#" -gt 1 ]]; then
  echo 'Usage: bash tools/build_local.sh [private-Gothic3.jar]' >&2
  exit 2
fi
ROOT=$(cd "$(dirname "$0")/.." && pwd)

if [[ "$#" -eq 1 ]]; then
  GAME_JAR=$(realpath "$1")
  python3 "$ROOT/tools/prepare_midlet.py" --jar "$GAME_JAR" --upstream "$ROOT"
fi

if ! python3 -c 'import PIL.Image' >/dev/null 2>&1; then
  echo 'Pillow required for launcher icons: python3 -m pip install Pillow==11.3.0' >&2
  exit 1
fi

cd "$ROOT"
python3 tools/generate_game_icons.py
chmod +x gradlew
./gradlew :app:testMidletDebugUnitTest :app:assembleMidletDebug --stacktrace
echo 'Gothic 3: The Beginning debug APK:'
find app/build/outputs/apk/midlet/debug -name '*.apk' -type f -print
