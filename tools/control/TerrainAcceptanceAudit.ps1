[CmdletBinding()]
param([string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path)
$ErrorActionPreference = 'Stop'
$atlas = Join-Path $Root 'assets\generated\worldgen_v0_1\terrain\lpc_mapped_terrain_v7_32.png'
$manifestPath = Join-Path $Root 'assets\generated\worldgen_v0_1\terrain\lpc_mapped_terrain_v7_32.json'
$acceptancePath = Join-Path $Root 'content\terrain\havenwild_terrain_acceptance_v1.json'
$reportDir = Join-Path $Root 'docs\audits\generated'
New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
foreach($required in @($atlas,$manifestPath,$acceptancePath)) {
  if(-not (Test-Path -LiteralPath $required)) { throw "Missing terrain acceptance input: $required" }
}
$manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
$acceptance = Get-Content -Raw -LiteralPath $acceptancePath | ConvertFrom-Json
$exact = @($manifest.entries | Where-Object { $_.topology -ne 'fill' }).Count
$fills = @($manifest.entries | Where-Object { $_.topology -eq 'fill' }).Count
$hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $atlas).Hash.ToLowerInvariant()
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$report = Join-Path $reportDir "terrain-acceptance-$stamp.md"
@"
# Havenwild Terrain Acceptance Audit

- Atlas: `$($manifest.output)`
- Atlas SHA-256: `$hash`
- Manifest entries: `$(@($manifest.entries).Count)`
- Exact/mixed entries: `$exact`
- Fill entries: `$fills`
- Acceptance scenarios: `$(@($acceptance.scenarios).Count)`
- Runtime policy: `$($manifest.runtimePolicy)`

## Required scenarios
$((@($acceptance.scenarios) | ForEach-Object { "- **$($_.id)** - $($_.required)" }) -join "`n")

This audit is diagnostic and does not add a mandatory build gate.
"@ | Set-Content -Encoding UTF8 -LiteralPath $report
Write-Host "Terrain acceptance audit written: $report" -ForegroundColor Green
Write-Host "Atlas entries: $(@($manifest.entries).Count); scenarios: $(@($acceptance.scenarios).Count)" -ForegroundColor Cyan
