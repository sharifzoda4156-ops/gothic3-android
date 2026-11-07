# Gothic 3: The Beginning — standalone Android fan port

An unofficial, non-commercial Gothic 3: The Beginning Android port built on the J2ME Loader midlet flavor (upstream Apache-2.0). Original game assets and trademarks belong to their respective rights holders.

## Build status and sources

GitHub Actions compiles a game-bearing APK directly from this repository, runs source/JVM/HD audits, and verifies the resulting APK. **A green build is not a substitute for on-device gameplay acceptance.**

**Important:** the current public Git history contains game code and images. Verify redistribution rights and use a private repository for any material you cannot distribute. Simply deleting files in a later commit does not delete them from history.

## What's included in the Android midlet flavor

- Gothic-specific first-launch profile created automatically; the J2ME Loader settings wizard does not interrupt the game launch.
- Stored profile defaults: 480×640 portrait, aspect-preserving scaling, fullscreen, Gothic backdrop, no stock emulator keyboard, keep screen awake.
- **HD×3 rendering preserved:** the 240×320 game world uses a 720×960 internal virtual display, irrespective of the stored 480×640 profile defaults. This is intentional for the latest HD×3 renderer; it is not an Android physical display resolution request.
- Dedicated Gothic stone-and-bronze controls below the game, not overlapping the MIDlet canvas: fixed eight-direction joystick, action (5), target (*), slots (#), left/right soft keys and pause (0).
- Top-row buttons ordered **Назад | Пауза | Меню**. Multitouch, held-key repeats, animated feedback and gentle device haptics.
- Android name **Gothic 3: The Beginning** and branded launcher from `app/src/midlet/resources/hd/icon.png`. Generated at build time.
- Canonical HD asset resolver, 3× character/world drawing and the most recently merged HD assets remain in `main`-based builds.

## Build the current project (never clone unmodified J2ME Loader for final APKs)

Requirements: JDK 21, Android SDK `platforms;android-37.0`, build-tools 37.0.0, NDK 29.0.14206865, Python 3 + `Pillow==11.3.0`, and Gradle dependencies.

Install Pillow: `python3 -m pip install Pillow==11.3.0` (Windows: `python -m pip install Pillow==11.3.0`).

From this repository's root:

- Linux/macOS/WSL: `bash tools/build_local.sh`
- Windows PowerShell: `.\tools\build_local.ps1`

**Do not supply the original private game JAR to these ordinary build commands.** The checked-in tree already contains current game and HD×3 components. Using the old script that clones vanilla J2ME Loader, or preparing an older JAR over current files, loses the custom native keyboard and game enhancements.

The resulting Android APK is under `app/build/outputs/apk/midlet/debug/`; CI uploads it as the `Gothic_3_The_Beginning_HD_APK` artifact. Use `tools/prepare_midlet.py` *explicitly and only for intentional game payload replacement*, after preserving the current HD payload.

## Verification

```bash
python3 -m unittest discover -s tests -v
python3 tools/audit_hd_assets.py
python3 tools/test_hd_routing.py
python3 tools/generate_game_icons.py
./gradlew :app:testMidletDebugUnitTest :app:assembleMidletDebug
python3 tools/verify_standalone_apk.py --apk app/build/outputs/apk/midlet/debug/NAME-debug.apk
```

The APK verifier checks compiled DEX for the native controls, Gothic profile and HD×3 renderer, rather than merely assuming that source code is present. CI also checks the Android application label and game resource assets.

Use `tools/android_smoke.sh /path/to/Gothic3-debug.apk` for manual Android ADB acceptance. Test first launch, combat, joystick and simultaneous touch, pause/back/menu, HD graphics, sound, saves, and runtime logs before merging changes.

## Attribution

J2ME Loader remains subject to upstream Apache-2.0 licensing. Original Gothic game media are not licensed through this project.
