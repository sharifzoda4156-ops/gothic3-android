# Build standalone Gothic 3 directly from the current modified repository.
# Optional replacement JAR is processed locally; no external upstream checkout is built.
param(
    [string]$JarPath = ""
)

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

    if ($JarPath) {
        $FullJarPath = (Resolve-Path $JarPath).Path
        python "$BuildRoot\tools\prepare_midlet.py" --jar "$FullJarPath" --upstream "$BuildRoot"
        if ($LASTEXITCODE -ne 0) { throw "Game JAR preparation failed" }
    }

    python -c "import PIL.Image"
    if ($LASTEXITCODE -ne 0) {
        throw "Pillow is required: python -m pip install Pillow==11.3.0"
    }

    python "$BuildRoot\tools\generate_game_icons.py" --source "$BuildRoot\app\src\midlet\resources\hd\icon.png" --output "$BuildRoot\app\src\midlet\res"
    if ($LASTEXITCODE -ne 0) { throw "Gothic launcher icon generation failed" }

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

    Write-Host "Gothic 3: The Beginning - $($Apk.FullName)"
    Get-FileHash -Algorithm SHA256 $Apk.FullName
} finally {
    if ($SubstG) { subst G: /D }
    if ($SubstS) { subst S: /D }
}
