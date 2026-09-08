[CmdletBinding()]
param([string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path)

$ErrorActionPreference = 'Stop'
$registryPath = Join-Path $Root 'content\terrain\havenwild_terrain_gameplay_v1.json'
$corePath = Join-Path $Root 'crates\haven_core\src\terrain_contract.rs'
$foundationPath = Join-Path $Root 'crates\haven_core\src\foundation.rs'
$outDir = Join-Path $Root 'docs\audits\generated'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

if(-not (Test-Path $registryPath)){ throw "Missing terrain gameplay registry: $registryPath" }
if(-not (Test-Path $corePath)){ throw "Missing terrain contract: $corePath" }
if(-not (Test-Path $foundationPath)){ throw "Missing map consumer layer: $foundationPath" }

$registry = Get-Content $registryPath -Raw | ConvertFrom-Json
$profiles = @($registry.profiles)
$duplicates = $profiles | Group-Object tileKind | Where-Object Count -gt 1
$missingFields = @()
foreach($profile in $profiles){
  foreach($field in @('tileKind','collisionClass','waterDepth','movementCost','farmingClass','diggingClass','buildingClass','footstepSurface')){
    if($null -eq $profile.$field -or "$($profile.$field)" -eq ''){
      $missingFields += "$($profile.tileKind):$field"
    }
  }
}

$coreText = Get-Content $corePath -Raw
$foundationText = Get-Content $foundationPath -Raw
$consumerIntegration =
  $foundationText.Contains('terrain_movement_cost_at') -and
  $foundationText.Contains('terrain_farming_class_at') -and
  $foundationText.Contains('terrain_footstep_surface_at') -and
  $foundationText.Contains('terrain_allows_standard_building_at') -and
  $foundationText.Contains('collision_at_with_water_access')

$visualAuthoritySafe =
  $coreText.Contains('terrain_gameplay_profile') -and
  $coreText.Contains('base_terrain(tile)') -and
  -not $registry.rules.tupleArtworkOwnsGameplay -and
  -not $registry.rules.shaderMaterialOwnsGameplay

$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$reportPath = Join-Path $outDir "terrain-gameplay-audit-$timestamp.md"
$status = if($profiles.Count -eq 32 -and $duplicates.Count -eq 0 -and $missingFields.Count -eq 0 -and $visualAuthoritySafe -and $consumerIntegration){ 'PASS' } else { 'WARN' }

@"
# Havenwild Terrain Gameplay Audit

- Status: **$status**
- Profiles: $($profiles.Count)
- Duplicate TileKinds: $($duplicates.Count)
- Missing fields: $($missingFields.Count)
- Semantic authority enforced: $visualAuthoritySafe
- Gameplay consumers integrated: $consumerIntegration

## Authority

Gameplay and collision are derived from semantic `TileKind` through
`terrain_gameplay_profile`. Tuple artwork and shader materials remain
presentation-only.

## Coverage

- Walkable ground: $(($profiles | Where-Object collisionClass -eq 'walkable_ground').Count)
- Water: $(($profiles | Where-Object collisionClass -eq 'water').Count)
- Solid: $(($profiles | Where-Object collisionClass -eq 'solid').Count)
- Fishable: $(($profiles | Where-Object fishable -eq $true).Count)
- Tillable: $(($profiles | Where-Object farmingClass -eq 'tillable').Count)
- Building forbidden: $(($profiles | Where-Object buildingClass -eq 'forbidden').Count)

## Missing fields

$($missingFields -join "`n")
"@ | Set-Content -Path $reportPath -Encoding UTF8

Write-Host "Terrain gameplay audit: $status" -ForegroundColor $(if($status -eq 'PASS'){'Green'}else{'Yellow'})
Write-Host "Report: $reportPath"
