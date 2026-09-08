$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\..')).Path
$Python = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } elseif (Get-Command python3 -ErrorAction SilentlyContinue) { "python3" } else { throw "python or python3 is required" }
Push-Location $Root
try {
    & $Python "tools/automation/validation/checks/editor/Validate-AssetIntakeAtlasAuthoringV66.py"
    exit $LASTEXITCODE
}
finally { Pop-Location }
