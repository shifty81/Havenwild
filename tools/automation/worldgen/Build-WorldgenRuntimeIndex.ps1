$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Script = Join-Path $RepoRoot "scripts\Build-WorldgenRuntimeIndex.py"
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) { throw "Python was not found." }
Push-Location $RepoRoot
try {
    if ($python.Name -eq "py.exe" -or $python.Name -eq "py") { & $python.Source -3 $Script } else { & $python.Source $Script }
    if ($LASTEXITCODE -ne 0) { throw "Worldgen runtime index build/probe failed." }
} finally { Pop-Location }
