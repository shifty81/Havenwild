$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\..')).Path
Push-Location $Root
try {
    python .\scripts\Validate-WorldgenFootprintsV06.py
} finally {
    Pop-Location
}
