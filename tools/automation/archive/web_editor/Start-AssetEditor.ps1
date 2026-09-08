param(
    [int]$Port = 4177
)

$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$Server = Join-Path $Root "web\editor\server.mjs"
$CatalogScript = Join-Path $Root "tools/automation/assets\Generate-AssetCatalog.ps1"

if (!(Test-Path $Server)) {
    throw "Asset Editor server not found: $Server"
}

if (Test-Path $CatalogScript) {
    & powershell -ExecutionPolicy Bypass -File $CatalogScript
}

Write-Host "Starting Web Editor on http://127.0.0.1:$Port/web/editor/index.html"
node $Server -Port $Port
