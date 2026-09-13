[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$Root,
  [string]$BranchName = 'experiment/asset-mapper-workspace'
)

$ErrorActionPreference = 'Stop'
$resolvedRoot = (Resolve-Path -LiteralPath $Root).Path
$gitDir = Join-Path $resolvedRoot '.git'
if (-not (Test-Path -LiteralPath $gitDir)) {
  throw "Cannot create Havenwild experiment branch because this root is not a Git checkout: $resolvedRoot"
}

$dirty = & git -C $resolvedRoot status --porcelain
if ($LASTEXITCODE -ne 0) { throw 'git status failed.' }
if ($dirty) {
  Write-Host '[BLOCKED] Working tree has uncommitted changes.' -ForegroundColor Yellow
  Write-Host 'Run the Full Quality Gate and commit/push the current GREEN state before switching branches.'
  Write-Host 'This keeps main as the stable lane and prevents experimental mapper work from contaminating a known-good checkpoint.'
  exit 2
}

$current = (& git -C $resolvedRoot rev-parse --abbrev-ref HEAD).Trim()
& git -C $resolvedRoot rev-parse --verify --quiet $BranchName *> $null
$existsCode = $LASTEXITCODE
if ($existsCode -eq 0) {
  Write-Host "Switching from $current to existing branch $BranchName"
  & git -C $resolvedRoot checkout $BranchName
} else {
  Write-Host "Creating experiment branch $BranchName from $current"
  & git -C $resolvedRoot checkout -b $BranchName
}
if ($LASTEXITCODE -ne 0) { throw "Failed to switch to $BranchName" }

$newCurrent = (& git -C $resolvedRoot rev-parse --abbrev-ref HEAD).Trim()
Write-Host "[PASS] Current branch: $newCurrent"
Write-Host 'Use the normal PCC Full Gate and Commit + Push GREEN flow on this branch.'
