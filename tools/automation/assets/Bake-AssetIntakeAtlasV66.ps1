$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$Python = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } elseif (Get-Command python3 -ErrorAction SilentlyContinue) { "python3" } else { throw "python or python3 is required" }
Push-Location $Root
try {
    & $Python "tools/automation/assets/Bake-AssetIntakeAtlasV66.py" @args
    exit $LASTEXITCODE
}
finally { Pop-Location }
