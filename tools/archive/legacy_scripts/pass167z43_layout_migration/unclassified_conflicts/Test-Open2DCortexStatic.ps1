[CmdletBinding()]
param([string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path)

$ErrorActionPreference = "Stop"
$required = @(
 "apps\open2d_cortex\Cargo.toml",
 "apps\cortex\Cargo.toml",
 "apps\cortex_desktop\Cargo.toml",
 "crates\cortex_cli\Cargo.toml",
 "crates\cortex_workspace\Cargo.toml",
 "crates\cortex_service\Cargo.toml",
 "crates\cortex_adapter_open2d\Cargo.toml",
 "crates\cortex_adapter_git\Cargo.toml",
 "crates\cortex_conversation\Cargo.toml",
 "crates\cortex_vault\Cargo.toml",
 "crates\cortex_plugin\Cargo.toml",
 "crates\cortex_desktop_core\Cargo.toml",
 "crates\cortex_client\Cargo.toml",
 "crates\cortex_activity\Cargo.toml",
 "crates\cortex_review\Cargo.toml",
 "crates\cortex_task\Cargo.toml",
 "crates\cortex_settings\Cargo.toml",
 "crates\cortex_artifacts\Cargo.toml",
 "crates\cortex_desktop_native\Cargo.toml",
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
 "schemas\cortex_plugin_manifest.v1.json",
 "schemas\cortex_permissions.v1.json",
 "schemas\cortex_desktop_state.v1.json",
 "schemas\cortex_desktop_state.v2.json",
 "schemas\cortex_settings.v1.json",
 "schemas\cortex_activity.v1.json",
 "schemas\cortex_task.v1.json",
 "schemas\cortex_review.v1.json",
 "schemas\cortex_desktop_certification.v1.json",
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


# Windows cmd.exe can misinterpret a UTF-8 BOM before `@echo off`, causing every
# menu command to echo visibly. Batch/control files are therefore certified
# BOM-free.
$batchFiles = @(
  Get-ChildItem -LiteralPath $RepoRoot -Recurse -File |
    Where-Object {
      ($_.Extension -ieq '.cmd' -or $_.Extension -ieq '.bat') -and
      $_.FullName -notmatch '\\target\\' -and
      $_.FullName -notmatch '\\node_modules\\' -and
      $_.FullName -notmatch '\\.git\\' -and
      $_.FullName -notmatch '\\.open2d\\' -and
      $_.FullName -notmatch '\\.cortex\\' -and
      $_.FullName -notmatch '\\logs\\' -and
      $_.FullName -notmatch '\\build\\' -and
      $_.FullName -notmatch '\\builds\\' -and
      $_.FullName -notmatch '\\dist\\'
    }
)
$batchEncodingFailures = @()
$batchReadFailures = @()
foreach ($file in $batchFiles) {
  try {
    $bytes = [System.IO.File]::ReadAllBytes($file.FullName)
  } catch {
    $batchReadFailures += @{
      Path = $file.FullName.Substring($RepoRoot.Length).TrimStart('\')
      Error = $_.Exception.Message
    }
    continue
  }

  if ($bytes.Length -ge 3 -and
      $bytes[0] -eq 0xEF -and
      $bytes[1] -eq 0xBB -and
      $bytes[2] -eq 0xBF) {
    $batchEncodingFailures += $file.FullName.Substring($RepoRoot.Length).TrimStart('\')
  }
}

if ($batchReadFailures.Count -gt 0) {
  Write-Host "Batch/control read certification FAILED." -ForegroundColor Red
  foreach ($failure in $batchReadFailures) {
    Write-Host (" - unable to read " + $failure.Path + ": " + $failure.Error)
  }
  exit 1
}
if ($batchEncodingFailures.Count -gt 0) {
  Write-Host "Batch/control encoding certification FAILED." -ForegroundColor Red
  $batchEncodingFailures | ForEach-Object {
    Write-Host (" - UTF-8 BOM is not allowed in Windows batch file: " + $_)
  }
  exit 1
}
Write-Host ("[PASS] Windows batch/control files are BOM-free: " + $batchFiles.Count + " files")

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

$cliSource = Get-Content -LiteralPath (Join-Path $RepoRoot "crates\cortex_cli\src\lib.rs") -Raw
$requiredCliMarkers = @(
  '"inspect" | "plan" | "apply" | "repair"',
  '"build" =>',
  '"session" =>',
  '"logs" =>',
  '"certify" =>',
  'OutputMode::Jsonl',
  'build.certify',
  'service_lifecycle_command',
  'git_command',
  'vault_command',
  'plugin_command',
  'desktop_command',
  'settings_command',
  'review_command',
  'activity_command',
  'tasks_command'
)
foreach ($marker in $requiredCliMarkers) {
  if (-not $cliSource.Contains($marker)) {
    Write-Host ("Cortex CLI contract marker missing: " + $marker) -ForegroundColor Red
    exit 1
  }
}
Write-Host "[PASS] Cortex CLI production-hardening markers present"


$desktopCoreSource = Get-Content -LiteralPath (Join-Path $RepoRoot "crates\cortex_desktop_core\src\lib.rs") -Raw
$desktopNativeSource = Get-Content -LiteralPath (Join-Path $RepoRoot "crates\cortex_desktop_native\src\lib.rs") -Raw
$desktopMarkers = @(
  'DesktopController',
  'send_chat',
  'run_agent',
  'show_changes',
  'search_vault',
  'run_build_check',
  'DesktopCertificationReport'
)
foreach ($marker in $desktopMarkers) {
  if (-not $desktopCoreSource.Contains($marker)) {
    Write-Host ("Cortex Desktop core contract marker missing: " + $marker) -ForegroundColor Red
    exit 1
  }
}
foreach ($marker in @('ID_INSPECT','ID_PLAN','ID_APPLY','ID_REPAIR','ID_SETTINGS')) {
  if (-not $desktopNativeSource.Contains($marker)) {
    Write-Host ("Cortex native desktop marker missing: " + $marker) -ForegroundColor Red
    exit 1
  }
}
Write-Host "[PASS] Cortex Desktop Chat + Codex shell markers present"


# Standalone Cortex compatibility-layer contract checks.
$workspaceFacadeCargo = Get-Content -LiteralPath (Join-Path $RepoRoot "crates\open2d_cortex_workspace\Cargo.toml") -Raw
$workspaceFacadeSource = Get-Content -LiteralPath (Join-Path $RepoRoot "crates\open2d_cortex_workspace\src\lib.rs") -Raw
$imageSource = Get-Content -LiteralPath (Join-Path $RepoRoot "crates\open2d_cortex_image\src\lib.rs") -Raw
$devSessionSource = Get-Content -LiteralPath (Join-Path $RepoRoot "crates\open2d_dev_session\src\lib.rs") -Raw

if (-not $workspaceFacadeCargo.Contains('cortex_workspace = { path = "../cortex_workspace" }')) {
  Write-Host "[FAIL] open2d_cortex_workspace is not wired to standalone cortex_workspace." -ForegroundColor Red
  exit 1
}
if (-not $workspaceFacadeSource.Contains('pub use cortex_workspace::*;')) {
  Write-Host "[FAIL] open2d_cortex_workspace is not the standalone compatibility facade." -ForegroundColor Red
  exit 1
}
foreach ($marker in @(
  'catalog_path_from_state',
  'metadata_root_from_state',
  'generated_output_root_from_state'
)) {
  if (-not $imageSource.Contains($marker)) {
    Write-Host ("[FAIL] Cortex image state-root contract missing: " + $marker) -ForegroundColor Red
    exit 1
  }
}
if (-not $devSessionSource.Contains('pub fn create_in')) {
  Write-Host "[FAIL] DevSession::create_in standalone session-root contract is missing." -ForegroundColor Red
  exit 1
}
Write-Host "[PASS] Standalone Cortex compatibility contracts synchronized"


# Cortex executable entrypoint authority checks.
$open2dCortexMain = Get-Content -LiteralPath (Join-Path $RepoRoot "apps\open2d_cortex\src\main.rs") -Raw
$standaloneCortexMain = Get-Content -LiteralPath (Join-Path $RepoRoot "apps\cortex\src\main.rs") -Raw
$open2dCortexCargo = Get-Content -LiteralPath (Join-Path $RepoRoot "apps\open2d_cortex\Cargo.toml") -Raw
$standaloneCortexCargo = Get-Content -LiteralPath (Join-Path $RepoRoot "apps\cortex\Cargo.toml") -Raw

foreach ($entry in @(
  @{ Name = "apps/open2d_cortex"; Main = $open2dCortexMain; Cargo = $open2dCortexCargo },
  @{ Name = "apps/cortex"; Main = $standaloneCortexMain; Cargo = $standaloneCortexCargo }
)) {
  if (-not $entry.Main.Contains('cortex_cli::main_entry();')) {
    Write-Host ("[FAIL] " + $entry.Name + " is not a thin cortex_cli entrypoint.") -ForegroundColor Red
    exit 1
  }
  if ($entry.Main.Contains('ToolBroker::new') -or
      $entry.Main.Contains('LmStudioProvider') -or
      $entry.Main.Contains('AgentEngine')) {
    Write-Host ("[FAIL] " + $entry.Name + " contains duplicated Cortex construction logic.") -ForegroundColor Red
    exit 1
  }
  if (-not $entry.Cargo.Contains('cortex_cli = { path = "../../crates/cortex_cli" }')) {
    Write-Host ("[FAIL] " + $entry.Name + " does not depend on the canonical cortex_cli authority.") -ForegroundColor Red
    exit 1
  }
}
Write-Host "[PASS] Cortex executable entrypoints are thin cortex_cli wrappers"


# Cortex desktop/service launch contract checks.
$serviceSource = Get-Content -LiteralPath (Join-Path $RepoRoot "crates\cortex_service\src\lib.rs") -Raw
foreach ($marker in @(
  'pub fn spawn_executable(',
  'pub fn spawn_executable_with_env(',
  'environment: &[(String, String)]'
)) {
  if (-not $serviceSource.Contains($marker)) {
    Write-Host ("[FAIL] Cortex service desktop-launch contract missing: " + $marker) -ForegroundColor Red
    exit 1
  }
}
if ($serviceSource.Contains('trim().to_string())')) {
  Write-Host "[FAIL] Cortex service contains the Clippy-rejected owned path conversion." -ForegroundColor Red
  exit 1
}
Write-Host "[PASS] Cortex desktop/service launch contract synchronized"


# Clippy-critical std::io::Lines consumption guard.
$linesFilterMapHits = @(
  Get-ChildItem -LiteralPath (Join-Path $RepoRoot "crates") -Recurse -File -Filter *.rs |
    Where-Object {
      $_.FullName -match '\\cortex_' -or
      $_.FullName -match '\\open2d_cortex_'
    } |
    ForEach-Object {
      $source = Get-Content -LiteralPath $_.FullName -Raw
      if ($source -match '\.lines\(\)\s*\.filter_map\(Result::ok\)') {
        $_.FullName.Substring($RepoRoot.Length).TrimStart('\')
      }
    }
)
if ($linesFilterMapHits.Count -gt 0) {
  Write-Host "[FAIL] Clippy-critical lines().filter_map(Result::ok) pattern found:" -ForegroundColor Red
  foreach ($hit in $linesFilterMapHits) {
    Write-Host (" - " + $hit)
  }
  Write-Host "Use lines().map_while(Result::ok) for std::io::Lines." -ForegroundColor Yellow
  exit 1
}
Write-Host "[PASS] Cortex std::io::Lines consumption is Clippy-safe"


# Cortex agent-context and checkpoint-isolation guards.
$coreSource = Get-Content -LiteralPath (Join-Path $RepoRoot "crates\open2d_cortex_core\src\lib.rs") -Raw
$cliSource = Get-Content -LiteralPath (Join-Path $RepoRoot "crates\cortex_cli\src\lib.rs") -Raw
$toolsSource = Get-Content -LiteralPath (Join-Path $RepoRoot "crates\open2d_cortex_tools\src\lib.rs") -Raw
$toolsCmd = Get-Content -LiteralPath (Join-Path $RepoRoot "Open2DTools.cmd") -Raw

foreach ($marker in @(
  'max_tool_result_bytes',
  'fn bound_tool_result(',
  '"truncated": true'
)) {
  if (-not $coreSource.Contains($marker)) {
    Write-Host ("[FAIL] Cortex context-bound contract missing: " + $marker) -ForegroundColor Red
    exit 1
  }
}
if (-not $cliSource.Contains('ensure_active_transaction(self, action, reuse_transaction)')) {
  Write-Host "[FAIL] Cortex RPC Apply/Repair does not enforce durable transaction parity." -ForegroundColor Red
  exit 1
}
if (-not $toolsSource.Contains('unwrap_or(64 * 1024).clamp(1, 256 * 1024)')) {
  Write-Host "[FAIL] Cortex source.read safe default/cap is missing." -ForegroundColor Red
  exit 1
}
if (-not $toolsCmd.Contains('target\cortex-checkpoint')) {
  Write-Host "[FAIL] Cortex checkpoint does not use an isolated Cargo target directory." -ForegroundColor Red
  exit 1
}
Write-Host "[PASS] Cortex Apply context and checkpoint isolation contracts synchronized"

# Parse machine-readable contract files now so malformed JSON is caught before Cargo.
Get-Content -LiteralPath $toolSchemaPath -Raw | ConvertFrom-Json | Out-Null
Get-Content -LiteralPath (Join-Path $RepoRoot "schemas\cortex_cli_events.v1.json") -Raw | ConvertFrom-Json | Out-Null
Get-Content -LiteralPath (Join-Path $RepoRoot "schemas\cortex_plugin_manifest.v1.json") -Raw | ConvertFrom-Json | Out-Null
Get-Content -LiteralPath (Join-Path $RepoRoot "schemas\cortex_permissions.v1.json") -Raw | ConvertFrom-Json | Out-Null
Get-Content -LiteralPath (Join-Path $RepoRoot "schemas\cortex_desktop_state.v1.json") -Raw | ConvertFrom-Json | Out-Null
Get-Content -LiteralPath (Join-Path $RepoRoot "schemas\cortex_desktop_state.v2.json") -Raw | ConvertFrom-Json | Out-Null
Get-Content -LiteralPath (Join-Path $RepoRoot "schemas\cortex_settings.v1.json") -Raw | ConvertFrom-Json | Out-Null
Get-Content -LiteralPath (Join-Path $RepoRoot "schemas\cortex_activity.v1.json") -Raw | ConvertFrom-Json | Out-Null
Get-Content -LiteralPath (Join-Path $RepoRoot "schemas\cortex_task.v1.json") -Raw | ConvertFrom-Json | Out-Null
Get-Content -LiteralPath (Join-Path $RepoRoot "schemas\cortex_review.v1.json") -Raw | ConvertFrom-Json | Out-Null
Get-Content -LiteralPath (Join-Path $RepoRoot "schemas\cortex_desktop_certification.v1.json") -Raw | ConvertFrom-Json | Out-Null
Write-Host "[PASS] Cortex machine-readable schemas parse"

& (Join-Path $RepoRoot "scripts\Test-Open2DArchitecture.ps1") -RepoRoot $RepoRoot
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& (Join-Path $RepoRoot "scripts\Test-Open2DRootCleanliness.ps1") -RepoRoot $RepoRoot
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Cortex static certification: PASS" -ForegroundColor Green
