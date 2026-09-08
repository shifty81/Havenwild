$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\..')).Path
$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) { throw "python was not found on PATH" }
& $Python.Source (Join-Path $Root "scripts\Validate-WorldgenObjectOutlinerV08.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
