# PowerShell build script for Windows environments
param(
    [Parameter(Mandatory=$true)]
    [string]$JarPath
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$FullJarPath = (Resolve-Path $JarPath).Path

# Set up ASCII subst drive for project if needed to avoid NDK path issues
$SubstG = $false
$SubstS = $false

try {
    # Check if current path or SDK has non-ASCII characters
    $HasNonAscii = ($Root -match '[^\x00-\x7F]')
    $SdkPath = "$env:LOCALAPPDATA\Android\Sdk"
    $SdkNonAscii = ($SdkPath -match '[^\x00-\x7F]')

    if ($HasNonAscii -and !(Test-Path "G:\")) {
        subst G: "$Root"
        $SubstG = $true
        $BuildRoot = "G:"
    } else {
        $BuildRoot = $Root
    }

    if ($SdkNonAscii -and !(Test-Path "S:\")) {
        subst S: "$SdkPath"
        $SubstS = $true
        $env:ANDROID_HOME = "S:\"
    } else {
        $env:ANDROID_HOME = $SdkPath
    }

    # Set JAVA_HOME if Android Studio JBR exists
    $JbrPath = "C:\Program Files\Android\Android Studio\jbr"
    if (Test-Path $JbrPath) {
        $env:JAVA_HOME = $JbrPath
    }

    $Upstream = "$BuildRoot\.work\J2ME-Loader"
    $UpstreamSha = "261c216c017e77391774ca10748c1229884cecd2"

    if (!(Test-Path "$Upstream\.git")) {
        git clone https://github.com/nikita36078/J2ME-Loader.git "$Upstream"
    }

    git -C "$Upstream" fetch origin "$UpstreamSha"
    git -C "$Upstream" checkout "$UpstreamSha"
    git -C "$Upstream" submodule update --init --recursive

    python "$BuildRoot\tools\prepare_midlet.py" --jar "$FullJarPath" --upstream "$Upstream"

    Push-Location "$Upstream"
    try {
        .\gradlew.bat :app:assembleMidletDebug --stacktrace
    } finally {
        Pop-Location
    }

    $Apk = Get-ChildItem "$Upstream\app\build\outputs\apk\midlet\debug\*.apk" | Select-Object -First 1
    if ($Apk) {
        Write-Host "Build Successful: $($Apk.FullName)"
        Get-FileHash -Algorithm SHA256 $Apk.FullName
    }
} finally {
    if ($SubstG) { subst G: /D }
    if ($SubstS) { subst S: /D }
}
