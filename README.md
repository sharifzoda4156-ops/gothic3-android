# Gothic 3: The Beginning — Android fan port

**Status: standalone Android APK builds in CI; game launch and performance still require Android device verification.**

An unofficial, non-commercial fan project based on [J2ME Loader](https://github.com/nikita36078/J2ME-Loader), licensed under Apache-2.0. Gothic and the original game materials belong to their respective rights holders. The public repository has no game files.

## Gothic 3 launch behavior and launcher branding

For the `midlet` flavor, the game now creates its settings automatically on first launch instead of redirecting to the J2ME Loader configuration screen. The initial preset is **480×640 portrait**, 4:3 aspect-preserving fit, centered image, fullscreen, no blurring filter, black-brown letterboxing, dedicated native Gothic control deck, FPS counter hidden and screen-awake enabled.

Existing custom profiles are preserved. Previously untouched 240×320 profiles are migrated once to 480×640; user edits made afterwards are not overwritten. The J2ME Loader settings screen remains available from its normal in-game options for manual adjustments.

The Android application and MIDlet display name are **Gothic 3: The Beginning**. During the build, `tools/generate_game_icons.py` generates standard and adaptive Android launcher icons from the game's own `hd/icon.png` (the Gothic G emblem), replacing the generic J2ME Loader icon.

These settings are implementation defaults, not yet a verified on-device gameplay configuration.

## Native Gothic 3 touch controls (Android)

The standalone `midlet` build now has a **dedicated native control deck below the MIDlet display**, with no overlap over the gameplay image. This is not J2ME Loader's virtual keyboard or editable keyboard layout.

- Fixed, eight-way circular joystick with an inner movable knob, direction indicators and diagonal illumination. Its input uses the original MIDP number-pad directions 1/2/3/4/6/7/8/9, with a dead zone to avoid unintentional movement.
- Six dedicated touch targets: **ДЕЙСТВИЕ** (5), **ЦЕЛЬ** (*), **СЛОТЫ** (#), **МЕНЮ** (left soft), **НАЗАД** (right soft), **ПАУЗА** (0). The mapping for game-specific actions needs real-device playtesting.
- Gothic stone-and-bronze design with eased press depth, amber glow and animated spring-return joystick; compact iconography and text labels.
- Multitouch uses Android pointer IDs, so moving and using an action button simultaneously is supported.
- Light haptic feedback respects device-level haptic feedback settings. Pressed keys are released on pointer cancel, app pause, leaving gameplay canvas, and Activity destruction.
- Key repeat starts after a hold delay. Events are injected through the original MIDlet Canvas event queue (not Android key dispatch), preserving game-key handling.

The new control deck is only installed when `BuildConfig.FULL_EMULATOR == false`. Other J2ME Loader flavors retain their original behavior.

**Verification:** unit tests cover the eight-way direction map, dead zone and preset. The GitHub Actions APK build checks compilation; physical Android confirmation of touch latency, layout, menu bindings, joystick movement and haptics is still necessary.

## Standalone one-game plan

J2ME Loader already supports an Android product flavor named **midlet**, which launches one Java ME MIDlet without the general-purpose app picker. The helper scripts take a private Gothic game JAR and prepare the required layout inside a source checkout of J2ME Loader:

- Java classes become a Gradle dependency: app/libs/gothic3-classes.jar.
- Game assets become Java resources: app/src/midlet/resources/.
- Game manifest becomes: app/src/midlet/resources/MIDLET-META-INF/MANIFEST.MF.
- Package ID is set to org.gothic3.fanport.

This is NOT the earlier HD patch. HD renderer support and 4x art remain separate work and are not claimed as implemented.

## Build the current Gothic repository

Requirements: Git, Python 3 with Pillow 11.3.0, JDK 21, Android SDK platform `platforms;android-37.0`, build-tools 37.0.0 and Android NDK 29.0.14206865.

The repository contains the standalone game source setup. **Build the local checkout directly**, not a fresh unmodified J2ME Loader clone:

- Linux/macOS/WSL: `bash tools/build_local.sh`
- Windows PowerShell: `.\\tools\\build_local.ps1`

An optional private replacement JAR may be passed to either command; the preparation tool keeps the Gothic 3: The Beginning name.

Before local builds install Pillow: `python3 -m pip install Pillow==11.3.0` (Windows: `python -m pip install Pillow==11.3.0`).

CI performs the same branding generation and builds `:app:assembleMidletDebug`. The resulting file is under `app/build/outputs/apk/midlet/debug/`.

## Tests and remaining unknowns

Run the converter tests:

    python3 -m unittest discover -s tests -v

A Gothic-branded APK has compiled in GitHub Actions, and synthetic Java 46/52 D8 acceptance passed. **Real game launch, config autoload and runtime image loading have NOT been verified on Android.** Acceptance requires a real game launch with a working title screen, 005.png atlas, controls, sound, RMS saves, transitions, screenshots, and logcat.

## Static HD atlas audit

The privately supplied test JAR has a 2x HD atlas directory. Verify geometry offline, without publishing game assets:

    python3 tools/audit_hd_jar.py /absolute/path/to/your/Gothic3-test.jar

The audit checks doubled PNG dimensions and reports class-file versions. Correct 2x dimensions do not prove that the engine paints at HD resolution.

GitHub Actions compiles the game-bearing project. Its successful build does not prove that the Gothic title screen or HD assets display correctly on a device.

## Android smoke test (after a private APK build)

Connect and authorize an Android phone with USB debugging enabled, then execute:

    bash tools/android_smoke.sh /path/to/Gothic3-debug.apk

The script installs and launches the debug package, then captures a screenshot and logcat locally under `.work/`. This test is **not** automated gameplay validation; inspect controls, sound, save files and HD scenes manually.

## Attribution

J2ME Loader remains subject to its upstream Apache-2.0 license and notices. No commercial game art, code, or music is licensed for distribution through this project.