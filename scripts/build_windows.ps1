$ErrorActionPreference = 'Stop'
Push-Location (Split-Path $PSScriptRoot -Parent)
$felogramOriginalPath = $env:PATH
try {
    $felogramExecutable = [System.IO.Path]::GetFullPath(
        (Join-Path (Get-Location) 'dist\local\Felogram\Felogram.exe')
    )
    $felogramRunning = Get-Process Felogram -ErrorAction SilentlyContinue |
        Where-Object { $_.Path -eq $felogramExecutable }
    if ($felogramRunning) { throw 'Close the local Felogram bundle before rebuilding it.' }
    uv sync --locked --group package
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
    $felogramPythonRoot = & .\.venv\Scripts\python.exe -c 'import sys; print(sys.base_prefix)'
    $env:PATH = @(
        (Join-Path $env:SystemRoot 'System32'),
        $env:SystemRoot,
        $felogramPythonRoot,
        (Join-Path (Get-Location) '.venv\Scripts')
    ) -join ';'
    & .\.venv\Scripts\python.exe -m PyInstaller --noconfirm --onedir --console --name Felogram --paths src --distpath dist/local --collect-all tdjson src/felogram/__main__.py
    if ($LASTEXITCODE -ne 0) { throw 'Windows build failed' }
    & $felogramExecutable --probe
    if ($LASTEXITCODE -ne 0) { throw 'Packaged native probe failed' }
    & $felogramExecutable --smoke-test
    if ($LASTEXITCODE -ne 0) { throw 'Packaged desktop smoke test failed' }
    Write-Output 'Local bundle: dist\local\Felogram\Felogram.exe. End-user account checks remain manual.'
}
finally {
    $env:PATH = $felogramOriginalPath
    Pop-Location
}
