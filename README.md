# Gothic 3: The Beginning — Android fan port

**Status: source-side prototype. No Android APK has been compiled or tested yet.**

An unofficial, non-commercial fan project based on [J2ME Loader](https://github.com/nikita36078/J2ME-Loader), licensed under Apache-2.0. Gothic and the original game materials belong to their respective rights holders. The public repository has no game files.

## Standalone one-game plan

J2ME Loader already supports an Android product flavor named **midlet**, which launches one Java ME MIDlet without the general-purpose app picker. The helper scripts take a private Gothic game JAR and prepare the required layout inside a source checkout of J2ME Loader:

- Java classes become a Gradle dependency: app/libs/gothic3-classes.jar.
- Game assets become Java resources: app/src/midlet/resources/.
- Game manifest becomes: app/src/midlet/resources/MIDLET-META-INF/MANIFEST.MF.
- Package ID is set to org.gothic3.fanport.

This is NOT the earlier HD patch. HD renderer support and 4x art remain separate work and are not claimed as implemented.

## Local private Android build

Requirements: Git, Python 3, Bash, JDK 21, Android SDK 37, Android NDK 29.0.14206865, and the normal Gradle dependencies.

From the root of this repository, execute:

    bash tools/build_local.sh /absolute/path/to/your/Gothic3-test.jar

This pins J2ME Loader to commit 261c216c017e77391774ca10748c1229884cecd2, prepares the game classes and resources, then runs:

    ./gradlew :app:assembleMidletDebug

If successful, the APK will be inside .work/J2ME-Loader/app/build/outputs/apk/midlet/debug/.

**Never commit or upload the private Gothic JAR, game classes, extracted resources or APK to this public repository.** The GitHub Action runs only synthetic validation tests.

## Tests and remaining unknowns

Run the converter tests:

    python3 -m unittest discover -s tests -v

The actual APK build has NOT been run. Legacy Java 1.2 bytecode compatibility with D8 still needs to be checked, and the Android Java-resource lookup must be checked on-device. Acceptance requires a real game launch with a working title screen, 005.png atlas, controls, sound, RMS saves, transitions, screenshots, and logcat.

## Attribution

J2ME Loader remains subject to its upstream Apache-2.0 license and notices. No commercial game art, code, or music is licensed for distribution through this project.