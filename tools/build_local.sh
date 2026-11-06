#!/usr/bin/env bash
# Build a personal Android APK from a private Gothic JAR; do not commit game files.
set -euo pipefail
if [ "$#" -ne 1 ]; then
  echo "Usage: bash tools/build_local.sh /absolute/path/to/Gothic3-test.jar" >&2
  exit 2
fi
GAME_JAR=$(realpath "$1")
ROOT=$(cd "$(dirname "$0")/.." && pwd)
UPSTREAM="$ROOT/.work/J2ME-Loader"
UPSTREAM_SHA="261c216c017e77391774ca10748c1229884cecd2"
mkdir -p "$ROOT/.work"
if [ ! -d "$UPSTREAM/.git" ]; then
  git clone https://github.com/nikita36078/J2ME-Loader.git "$UPSTREAM"
fi
git -C "$UPSTREAM" fetch origin "$UPSTREAM_SHA"
git -C "$UPSTREAM" checkout --detach "$UPSTREAM_SHA"
git -C "$UPSTREAM" submodule update --init --recursive
# Android API 37 cannot currently be installed from the stable SDK repository.
# Use API 36 for a compatibility smoke build; targetSdk remains at upstream's 36.
ANDROID_API="${GOTHIC_ANDROID_API:-36}"
if [ "$ANDROID_API" != 36 ] && [ "$ANDROID_API" != 37 ]; then
  echo "GOTHIC_ANDROID_API must be 36 or 37" >&2
  exit 2
fi
sed -i "s/COMPILE_SDK = 37/COMPILE_SDK = $ANDROID_API/" "$UPSTREAM/build.gradle"
python3 "$ROOT/tools/prepare_midlet.py" --jar "$GAME_JAR" --upstream "$UPSTREAM"
cd "$UPSTREAM"
chmod +x gradlew
./gradlew :app:assembleMidletDebug --stacktrace
find app/build/outputs/apk/midlet/debug -name '*.apk' -type f -print
