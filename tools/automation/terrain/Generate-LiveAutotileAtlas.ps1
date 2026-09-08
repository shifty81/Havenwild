param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
Push-Location $Root
try {
    & $Python "tools/automation/terrain/Generate-LiveAutotileAtlas.py"
    if ($LASTEXITCODE -ne 0) {
        throw "Live autotile atlas generation failed with exit code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}
