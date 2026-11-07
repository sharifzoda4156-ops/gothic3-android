#!/usr/bin/env bash
# Build the Gothic Android app from this checkout. Optional private replacement JAR.
set -euo pipefail
if [[ "$#" -ne 0 ]]; then
  echo "Do not replace the HD3x game payload during an ordinary build. Run prepare_midlet.py explicitly if needed." >&2
  exit 2
fi
ROOT=$(cd "$(dirname "$0")/.." && pwd)

if ! python3 -c 'import PIL.Image' >/dev/null 2>&1; then
  echo 'Pillow required for launcher icons: python3 -m pip install Pillow==11.3.0' >&2
  exit 1
fi

cd "$ROOT"
python3 tools/generate_game_icons.py
python3 tools/audit_hd_assets.py
python3 tools/test_hd_routing.py
chmod +x gradlew
./gradlew :app:testMidletDebugUnitTest :app:assembleMidletDebug --stacktrace
for apk in app/build/outputs/apk/midlet/debug/*.apk; do
  python3 tools/audit_hd_assets.py --apk "$apk"
  python3 tools/verify_standalone_apk.py --apk "$apk"
done
echo 'Gothic 3: The Beginning debug APK:'
find app/build/outputs/apk/midlet/debug -name '*.apk' -type f -print
