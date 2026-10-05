[CmdletBinding()]
param(
    [string]$SourcePath = (Join-Path $PSScriptRoot '..\build\tdesktop-baseline'),
    [ValidateRange(1, 16)]
    [int]$BuildWorkers = 2,
    [switch]$PreflightOnly
)

$ErrorActionPreference = 'Stop'
$buildRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\build'))
$sourceRoot = (Resolve-Path -LiteralPath $SourcePath).Path
if ((Split-Path -Parent $sourceRoot) -ne $buildRoot) {
    throw 'Use an upstream checkout directly inside this project build directory.'
}
$inventory = & (Join-Path $PSScriptRoot 'check_native_windows.ps1') -SourcePath $sourceRoot
if ($LASTEXITCODE -ne 0) { throw 'Native compiler preflight failed; run check_native_windows.ps1 for details.' }
$configuration = $inventory | ConvertFrom-Json
Write-Output $inventory
if ($PreflightOnly) { return }

$compilerInstallation = $configuration.cppInstallations | Where-Object msvc1444Present | Select-Object -First 1
$vcvars = Join-Path $compilerInstallation.path 'VC\Auxiliary\Build\vcvars64.bat'
$prepareFile = Join-Path $sourceRoot 'Telegram\build\prepare\prepare.py'
if (-not (Test-Path -LiteralPath $vcvars) -or -not (Test-Path -LiteralPath $prepareFile)) {
    throw 'Compiler initialization or upstream preparation script is missing.'
}
$lockPath = Join-Path $buildRoot '.felogram-native-prepare.lock'
$lockStream = [IO.File]::Open($lockPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
$previousModules = $env:PSModulePath
$previousVcvars = $env:FELOGRAM_VCVARS
$previousPrepare = $env:FELOGRAM_PREPARE
$previousParallel = $env:CMAKE_BUILD_PARALLEL_LEVEL
Push-Location $sourceRoot
try {
    $env:PSModulePath = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\Modules;$env:ProgramFiles\WindowsPowerShell\Modules"
    $env:FELOGRAM_VCVARS = $vcvars
    $env:FELOGRAM_PREPARE = $prepareFile
    $env:CMAKE_BUILD_PARALLEL_LEVEL = $BuildWorkers.ToString()
    & "$env:SystemRoot\System32\cmd.exe" /d /v:off /c `
        'call "%FELOGRAM_VCVARS%" -vcvars_ver=14.44 && python -u "%FELOGRAM_PREPARE%" qt6 skip-release silent'
    if ($LASTEXITCODE -ne 0) { throw "Upstream dependency preparation failed with exit code $LASTEXITCODE." }
} finally {
    Pop-Location
    $env:PSModulePath = $previousModules
    $env:FELOGRAM_VCVARS = $previousVcvars
    $env:FELOGRAM_PREPARE = $previousPrepare
    $env:CMAKE_BUILD_PARALLEL_LEVEL = $previousParallel
    $lockStream.Dispose()
    Remove-Item -LiteralPath $lockPath
}
