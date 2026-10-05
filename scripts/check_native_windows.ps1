[CmdletBinding()]
param([string]$SourcePath = (Join-Path $PSScriptRoot '..\build\tdesktop-baseline'))

$ErrorActionPreference = 'Stop'
$vswherePath = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
$installations = @()
if (Test-Path -LiteralPath $vswherePath) {
    $installationJson = & $vswherePath -all -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -format json
    if ($LASTEXITCODE -ne 0) { throw 'Visual Studio inventory failed.' }
    $installations = @($installationJson | ConvertFrom-Json)
}
$sdkLib = Join-Path ${env:ProgramFiles(x86)} 'Windows Kits\10\Lib\10.0.26100.0\um\x64\kernel32.lib'
$gitCommand = Get-Command git -ErrorAction SilentlyContinue
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
$buildGuide = Join-Path $SourcePath 'docs\building-win.md'
$compatibleToolsets = @($installations | ForEach-Object {
    Get-ChildItem (Join-Path $_.installationPath 'VC\Tools\MSVC') -Directory `
        -Filter '14.44.*' -ErrorAction SilentlyContinue
})
$result = [ordered]@{
    checkedAt = (Get-Date).ToUniversalTime().ToString('o')
    sourcePath = [IO.Path]::GetFullPath($SourcePath)
    sourceGuidePresent = Test-Path -LiteralPath $buildGuide
    gitPresent = $null -ne $gitCommand
    pythonPresent = $null -ne $pythonCommand
    windowsSdk26100Present = Test-Path -LiteralPath $sdkLib
    msvc1444Present = $compatibleToolsets.Count -gt 0
    cppInstallations = @($installations | ForEach-Object {
        [ordered]@{ path = $_.installationPath; version = $_.installationVersion }
    })
    nativeBuildVerified = $false
}
$result | ConvertTo-Json -Depth 4
if ($installations.Count -eq 0 -or -not $result.msvc1444Present -or -not $result.windowsSdk26100Present -or
    -not $result.gitPresent -or -not $result.pythonPresent -or -not $result.sourceGuidePresent) {
    exit 1
}
# Presence alone does not prove the selected MSVC version or dependencies work.
exit 0
