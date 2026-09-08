[CmdletBinding()]
param([string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path)

$ErrorActionPreference = "Stop"
$required = @(
 "apps\open2d_cortex\Cargo.toml",
 "apps\open2d_ember\Cargo.toml",
 "crates\open2d_cortex_core\Cargo.toml",
 "crates\open2d_cortex_protocol\Cargo.toml",
 "crates\open2d_cortex_tools\Cargo.toml",
 "crates\open2d_cortex_provider_lmstudio\Cargo.toml",
 "crates\open2d_cortex_provider_comfyui\Cargo.toml",
 "crates\open2d_cortex_image\Cargo.toml",
 "crates\open2d_cortex_capture\Cargo.toml",
 "extensions\open2d-cortex-vscode\package.json",
 "schemas\cortex_tools.v1.json",
 "schemas\cortex_cli_events.v1.json",
 "scripts\Capture-Open2DWindow.ps1",
 "scripts\Repair-Open2DStaleLockfile.ps1",
 "scripts\Repair-Open2DPatchResidue.ps1",
 "scripts\New-Open2DDebugBundle.ps1",
 "docs\ai\BUILD_DEBUG_CHECKPOINT_R020.md"
)

$missing = @()
foreach ($relative in $required) {
  if (-not (Test-Path (Join-Path $RepoRoot $relative))) { $missing += $relative }
}
if ($missing.Count -gt 0) {
  Write-Host "Cortex static certification FAILED." -ForegroundColor Red
  $missing | ForEach-Object { Write-Host (" - missing " + $_) }
  exit 1
}

# The checked-in tool catalog is documentation/automation metadata. The Rust
# ToolBroker remains code authority, so static certification fails if they drift.
$toolSourcePath = Join-Path $RepoRoot "crates\open2d_cortex_tools\src\lib.rs"
$toolSource = Get-Content -LiteralPath $toolSourcePath -Raw
$actualTools = @(
  [regex]::Matches($toolSource, 'tool\("([^"]+)"') |
    ForEach-Object { $_.Groups[1].Value } |
    Sort-Object -Unique
)

$toolSchemaPath = Join-Path $RepoRoot "schemas\cortex_tools.v1.json"
$toolSchema = Get-Content -LiteralPath $toolSchemaPath -Raw | ConvertFrom-Json
$expectedTools = @()
foreach ($property in $toolSchema.tool_groups.PSObject.Properties) {
  $expectedTools += @($property.Value)
}
$expectedTools = @($expectedTools | Sort-Object -Unique)
$toolDiff = @(Compare-Object -ReferenceObject $expectedTools -DifferenceObject $actualTools)
if ($toolDiff.Count -gt 0) {
  Write-Host "Cortex tool catalog drift detected." -ForegroundColor Red
  $toolDiff | ForEach-Object {
    Write-Host (" - " + $_.SideIndicator + " " + $_.InputObject)
  }
  exit 1
}
Write-Host ("[PASS] Cortex tool catalog matches Rust authority: " + $actualTools.Count + " tools")

$cliSource = Get-Content -LiteralPath (Join-Path $RepoRoot "apps\open2d_cortex\src\main.rs") -Raw
$requiredCliMarkers = @(
  '"inspect" | "plan" | "apply" | "repair"',
  '"build" =>',
  '"session" =>',
  '"logs" =>',
  '"certify" =>',
  'OutputMode::Jsonl',
  'build.certify'
)
foreach ($marker in $requiredCliMarkers) {
  if (-not $cliSource.Contains($marker)) {
    Write-Host ("Cortex CLI contract marker missing: " + $marker) -ForegroundColor Red
    exit 1
  }
}
Write-Host "[PASS] Cortex CLI production-hardening markers present"

# Parse machine-readable contract files now so malformed JSON is caught before Cargo.
Get-Content -LiteralPath $toolSchemaPath -Raw | ConvertFrom-Json | Out-Null
Get-Content -LiteralPath (Join-Path $RepoRoot "schemas\cortex_cli_events.v1.json") -Raw | ConvertFrom-Json | Out-Null
Write-Host "[PASS] Cortex machine-readable schemas parse"

& (Join-Path $RepoRoot "scripts\Test-Open2DArchitecture.ps1") -RepoRoot $RepoRoot
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& (Join-Path $RepoRoot "scripts\Test-Open2DRootCleanliness.ps1") -RepoRoot $RepoRoot
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Cortex static certification: PASS" -ForegroundColor Green
