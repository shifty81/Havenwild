[CmdletBinding()]
param([string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path)

$ErrorActionPreference = 'Stop'
$outDir = Join-Path $Root 'docs\audits\generated'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$required = [ordered]@{
  GameplayRegistry = 'content\terrain\havenwild_terrain_gameplay_v1.json'
  TerrainStandard = 'content\terrain\havenwild_terrain_standard_v1.json'
  TupleCatalog = 'content\terrain\havenwild_terrain_tuple_catalog_v1.json'
  AcceptanceRegistry = 'content\terrain\havenwild_terrain_acceptance_v1.json'
  RuntimeAtlas = 'assets\generated\worldgen_v0_1\terrain\lpc_mapped_terrain_v7_32.png'
  RuntimeManifest = 'assets\generated\worldgen_v0_1\terrain\lpc_mapped_terrain_v7_32.json'
  TerrainContract = 'crates\haven_core\src\terrain_contract.rs'
  Foundation = 'crates\haven_core\src\foundation.rs'
  EditorInspector = 'apps\haven_editor_native\src\app\object_inspector.rs'
}

$missing = @()
foreach($entry in $required.GetEnumerator()){
  if(-not (Test-Path (Join-Path $Root $entry.Value))){
    $missing += "$($entry.Key): $($entry.Value)"
  }
}

$gameplay = Get-Content (Join-Path $Root $required.GameplayRegistry) -Raw | ConvertFrom-Json
$acceptance = Get-Content (Join-Path $Root $required.AcceptanceRegistry) -Raw | ConvertFrom-Json
$runtime = Get-Content (Join-Path $Root $required.RuntimeManifest) -Raw | ConvertFrom-Json
$coreText = Get-Content (Join-Path $Root $required.TerrainContract) -Raw
$foundationText = Get-Content (Join-Path $Root $required.Foundation) -Raw
$inspectorText = Get-Content (Join-Path $Root $required.EditorInspector) -Raw

$checks = [ordered]@{
  RequiredFilesPresent = ($missing.Count -eq 0)
  GameplayProfileCount = (@($gameplay.profiles).Count -eq 32)
  SemanticAuthority = (
    $coreText.Contains('terrain_gameplay_profile') -and
    -not $gameplay.rules.tupleArtworkOwnsGameplay -and
    -not $gameplay.rules.shaderMaterialOwnsGameplay
  )
  BuildingSupportPolicy = (
    $coreText.Contains('pub enum BuildingSupport') -and
    $coreText.Contains('pub const fn allows(self, support: BuildingSupport)') -and
    $foundationText.Contains('terrain_allows_foundation_at') -and
    $foundationText.Contains('terrain_allows_bridge_at')
  )
  RuntimeAtlasMapped = (
    $null -ne $runtime -and
    (Test-Path (Join-Path $Root $required.RuntimeAtlas))
  )
  EditorTupleInspector = (
    $inspectorText.Contains('Terrain Tuple Inspector') -and
    $inspectorText.Contains('Movement cost')
  )
  WrappedSeamScenario = (
    (Get-Content (Join-Path $Root $required.AcceptanceRegistry) -Raw).Contains('wrapped')
  )
}

$failed = @($checks.GetEnumerator() | Where-Object { -not $_.Value })
$status = if($failed.Count -eq 0){ 'PASS' } else { 'WARN' }
$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$report = Join-Path $outDir "terrain-certification-$timestamp.md"

$lines = @(
  '# Havenwild Terrain Certification',
  '',
  "- Status: **$status**",
  "- Checks: $($checks.Count)",
  "- Failed: $($failed.Count)",
  '',
  '## Results',
  ''
)
foreach($check in $checks.GetEnumerator()){
  $mark = if($check.Value){ 'PASS' } else { 'WARN' }
  $lines += "- $mark - $($check.Key)"
}
$lines += @(
  '',
  '## Missing files',
  ''
)
if($missing.Count -eq 0){ $lines += '- None' } else { $lines += $missing | ForEach-Object { "- $_" } }
$lines += @(
  '',
  '## Certification boundary',
  '',
  'This report certifies static project integration only. `tools/build/Build.cmd all` and',
  'live Windows editor/runtime inspection remain the authoritative executable',
  'certification steps.'
)
$lines | Set-Content -Path $report -Encoding UTF8

Write-Host "Terrain certification audit: $status" -ForegroundColor $(if($status -eq 'PASS'){'Green'}else{'Yellow'})
Write-Host "Report: $report"
