param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\..')).Path
Push-Location $Root
try {
    & $Python "tools/automation/validation/checks/assets/Validate-AssetPaletteAtlasBindingV65.py"
    if ($LASTEXITCODE -ne 0) {
        throw "Pass 52 asset palette and atlas-binding validation failed with exit code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}
