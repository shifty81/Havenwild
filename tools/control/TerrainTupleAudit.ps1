[CmdletBinding()]
param(
  [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
)
$ErrorActionPreference = 'Stop'
$catalogPath = Join-Path $Root 'content\terrain\havenwild_terrain_tuple_catalog_v1.json'
$policyPath = Join-Path $Root 'content\terrain\havenwild_terrain_duplicate_policy_v1.json'
if(-not (Test-Path $catalogPath)){ throw "Terrain tuple catalog missing: $catalogPath" }
if(-not (Test-Path $policyPath)){ throw "Terrain duplicate policy missing: $policyPath" }
$catalog = Get-Content $catalogPath -Raw | ConvertFrom-Json
$policy = Get-Content $policyPath -Raw | ConvertFrom-Json
$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$outDir = Join-Path $Root 'docs\audits\generated'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$outPath = Join-Path $outDir "terrain-tuple-audit-$timestamp.md"
$malformed = @()
foreach($property in $catalog.signatureToTileId.PSObject.Properties){
  if($property.Name -notmatch '^(_|\d+),(_|\d+),(_|\d+),(_|\d+)$'){
    $malformed += $property.Name
  }
}
$lines = @(
  '# Havenwild Terrain Tuple Audit',
  '',
  "Generated: $(Get-Date -Format o)",
  '',
  '## Catalog',
  '',
  "- Schema: $($catalog.schema)",
  "- Declared atlas tiles: $($catalog.declaredTileCount)",
  "- Mapped tuple entries: $($catalog.mappedTupleCount)",
  "- Unique signatures: $($catalog.uniqueSignatureCount)",
  "- Duplicate signatures: $($catalog.duplicateSignatureCount)",
  "- Terrain families: $($catalog.terrainOrdinalToCode.PSObject.Properties.Count)",
  "- Malformed signatures: $($malformed.Count)",
  '',
  '## Duplicate policy',
  '',
  "- Policy: $($policy.policy)",
  "- Classified duplicate records: $($policy.records.Count)",
  '',
  '## Result',
  ''
)
if($malformed.Count -eq 0 -and $policy.records.Count -eq $catalog.duplicateSignatureCount){
  $lines += '- PASS: catalog shape and duplicate classification are internally consistent.'
}else{
  $lines += '- WARNING: catalog shape or duplicate classification requires review.'
}
if($malformed.Count -gt 0){
  $lines += ''
  $lines += '## Malformed signatures'
  $lines += ''
  $lines += $malformed | ForEach-Object { "- ``$_``" }
}
$lines | Set-Content -Path $outPath -Encoding UTF8
Write-Host "Terrain tuple audit written: $outPath" -ForegroundColor Green
Write-Host "Unique=$($catalog.uniqueSignatureCount) Duplicate=$($catalog.duplicateSignatureCount) Malformed=$($malformed.Count)" -ForegroundColor Cyan
