[CmdletBinding()]
param([string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path)

$ErrorActionPreference = "Stop"
$legacy = Join-Path $RepoRoot "PATCH_MANIFEST.json"
if (-not (Test-Path -LiteralPath $legacy -PathType Leaf)) {
    Write-Host "Patch residue: no legacy root PATCH_MANIFEST.json detected."
    exit 0
}

$destinationDir = Join-Path $RepoRoot "docs\patch"
New-Item -ItemType Directory -Force -Path $destinationDir | Out-Null
$destination = Join-Path $destinationDir "O2D_LAST_APPLIED_PATCH_MANIFEST.json"
Copy-Item -LiteralPath $legacy -Destination $destination -Force
Remove-Item -LiteralPath $legacy -Force
Write-Host "Moved legacy root PATCH_MANIFEST.json to docs\patch\O2D_LAST_APPLIED_PATCH_MANIFEST.json" -ForegroundColor Green
exit 0
