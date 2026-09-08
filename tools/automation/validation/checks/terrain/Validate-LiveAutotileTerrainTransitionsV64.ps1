param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\..')).Path
Push-Location $Root
try {
    & $Python "tools/automation/validation/checks/terrain/Validate-LiveAutotileTerrainTransitionsV64.py"
    if ($LASTEXITCODE -ne 0) {
        throw "Pass 51 live autotile validation failed with exit code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}
