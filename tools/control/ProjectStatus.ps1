param([Parameter(Mandatory=$true)][string]$Root)
$ErrorActionPreference='Continue'
Write-Host "Havenwild root: $Root"
Write-Host "Root files: $((Get-ChildItem -LiteralPath $Root -File).Count)"
Write-Host "Cargo workspace: $(Test-Path (Join-Path $Root 'Cargo.toml'))"
Write-Host "Native editor source: $(Test-Path (Join-Path $Root 'apps\haven_editor_native'))"
Write-Host "Game source: $(Test-Path (Join-Path $Root 'crates\haven_game'))"
Write-Host "Logs: $(Join-Path $Root 'logs')"

$laneAuthority=Join-Path $PSScriptRoot 'DevelopmentLane.ps1'
if(Test-Path -LiteralPath $laneAuthority -PathType Leaf) {
  Write-Host ''
  & powershell -NoProfile -ExecutionPolicy Bypass -File $laneAuthority -Root $Root -Action Status
  if($LASTEXITCODE -ne 0) {
    Write-Host "Development lane status failed with exit code $LASTEXITCODE"
  }
} elseif(Get-Command git -ErrorAction SilentlyContinue) {
  Push-Location $Root
  try {
    Write-Host "Branch: $((& git symbolic-ref --quiet --short HEAD 2>$null) -join '')"
    git status --short
  } finally {
    Pop-Location
  }
}
