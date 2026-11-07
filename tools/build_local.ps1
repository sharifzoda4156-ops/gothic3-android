# Build standalone Gothic 3 directly from the current modified repository.
# Optional replacement JAR is processed locally; no external upstream checkout is built.
param()

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$SubstG = $false
$SubstS = $false

try {
    $BuildRoot = $Root
    if (($Root -match '[^\x00-\x7F]') -and !(Test-Path "G:\")) {
        subst G: "$Root"
        if ($LASTEXITCODE -ne 0) { throw "Failed to mount ASCII build path G:" }
        $SubstG = $true
        $BuildRoot = "G:"
    }

    $SdkPath = "$env:LOCALAPPDATA\Android\Sdk"
    if ($env:ANDROID_HOME) { $SdkPath = $env:ANDROID_HOME }
    if (($SdkPath -match '[^\x00-\x7F]') -and !(Test-Path "S:\")) {
        subst S: "$SdkPath"
        if ($LASTEXITCODE -ne 0) { throw "Failed to mount ASCII SDK path S:" }
        $SubstS = $true
        $env:ANDROID_HOME = "S:\"
    } else {
        $env:ANDROID_HOME = $SdkPath
    }

    # Build only the checked-in HD3x resources. An old private JAR would overwrite them.

    if (!$env:JAVA_HOME -and (Test-Path "C:\Program Files\Android\Android Studio\jbr")) {
        $env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"
    }

    python -c "import PIL.Image"
    if ($LASTEXITCODE -ne 0) {
        throw "Pillow is required: python -m pip install Pillow==11.3.0"
    }

    python "$BuildRoot\tools\generate_game_icons.py" --source "$BuildRoot\app\src\midlet\resources\hd\icon.png" --output "$BuildRoot\app\src\midlet\res"
    if ($LASTEXITCODE -ne 0) { throw "Gothic launcher icon generation failed" }

    python "$BuildRoot\tools\audit_hd_assets.py"
    if ($LASTEXITCODE -ne 0) { throw "HD asset audit failed" }
    python "$BuildRoot\tools\test_hd_routing.py"
    if ($LASTEXITCODE -ne 0) { throw "HD loader routing verification failed" }

    Push-Location "$BuildRoot"
    try {
        .\gradlew.bat :app:testMidletDebugUnitTest :app:assembleMidletDebug --stacktrace
        if ($LASTEXITCODE -ne 0) { throw "Gradle build failed ($LASTEXITCODE)" }
    } finally {
        Pop-Location
    }

    $Apk = Get-ChildItem "$BuildRoot\app\build\outputs\apk\midlet\debug\*.apk" |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (!$Apk) { throw "Gradle reported success but the Gothic APK was not found" }

    python "$BuildRoot\tools\audit_hd_assets.py" --apk "$($Apk.FullName)"
    if ($LASTEXITCODE -ne 0) { throw "HD APK audit failed" }
    python "$BuildRoot\tools\verify_standalone_apk.py" --apk "$($Apk.FullName)"
    if ($LASTEXITCODE -ne 0) { throw "Custom UI APK check failed" }
    Write-Host "Gothic 3: The Beginning - $($Apk.FullName)"
    Get-FileHash -Algorithm SHA256 $Apk.FullName
} finally {
    if ($SubstG) { subst G: /D }
    if ($SubstS) { subst S: /D }
}
