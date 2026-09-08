$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Validator = Join-Path $RepoRoot "scripts\Validate-WorldgenAssets.py"

if (-not (Test-Path $Validator)) {
    throw "Missing validator: $Validator"
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command py -ErrorAction SilentlyContinue
}
if (-not $python) {
    throw "Python was not found. Install Python 3 or run scripts/Validate-WorldgenAssets.py manually with your Python interpreter."
}

Push-Location $RepoRoot
try {
    if ($python.Name -eq "py.exe" -or $python.Name -eq "py") {
        & $python.Source -3 $Validator
    } else {
        & $python.Source $Validator
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Worldgen asset validation failed. See logs/worldgen_asset_validation_report.json"
    }
    Write-Host "Worldgen asset validation: PASS" -ForegroundColor Green
} finally {
    Pop-Location
}
