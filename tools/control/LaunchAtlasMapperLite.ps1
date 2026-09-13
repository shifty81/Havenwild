[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$Root
)

$ErrorActionPreference = 'Stop'
$resolvedRoot = (Resolve-Path -LiteralPath $Root).Path
$launcher = Join-Path $resolvedRoot 'tools\launch\HavenwildAtlasMapperLite.cmd'
$cargoToml = Join-Path $resolvedRoot 'Cargo.toml'

if (-not (Test-Path -LiteralPath $cargoToml -PathType Leaf)) {
  throw "Havenwild Atlas Mapper Lite cannot launch because Cargo.toml was not found at $cargoToml"
}

if (-not (Test-Path -LiteralPath $launcher -PathType Leaf)) {
  throw "Havenwild Atlas Mapper Lite launcher is missing: $launcher"
}

Write-Host "Launching Havenwild Atlas Mapper Lite from $resolvedRoot"
Push-Location $resolvedRoot
try {
  & $launcher
  $code = $LASTEXITCODE
  if ($null -eq $code) { $code = 0 }
  if ($code -ne 0) {
    throw "Havenwild Atlas Mapper Lite exited with code $code"
  }
} finally {
  Pop-Location
}
