# Canonical Havenwild Git bridge (HW-EXPERIMENTAL-LANE-32).
# Intentionally no param(...) block: accepts current and legacy Control Center
# argument shapes without parameter-binding drift.
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$action = 'Status'
$message = ''
$remote = ''
$positionals = New-Object System.Collections.Generic.List[string]

for($i=0; $i -lt $args.Count; $i++) {
  $raw = [string]$args[$i]
  $key = $raw.TrimStart('-').ToLowerInvariant()
  if($key -in @('root','projectroot','repositoryroot') -and ($i+1) -lt $args.Count) { $root = [string]$args[++$i]; continue }
  if($key -eq 'action' -and ($i+1) -lt $args.Count) { $action = [string]$args[++$i]; continue }
  if($key -in @('message','commitmessage') -and ($i+1) -lt $args.Count) { $message = [string]$args[++$i]; continue }
  if($key -in @('remote','remoteurl','url') -and ($i+1) -lt $args.Count) { $remote = [string]$args[++$i]; continue }
  if(-not $raw.StartsWith('-')) { $positionals.Add($raw) }
}

if($positionals.Count -gt 0 -and (Test-Path -LiteralPath $positionals[0])) { $root = $positionals[0] }
$known = @('Status','Setup','Init','Initialize','Connect','Repair','Adopt','Review','ReviewCore','ReviewGitHubCore','CommitGreen','CommitPushGreen','Push','PushMain','Pull','Open','OpenRepo','OpenRemote','CommitManual','ManualCommit','AdvancedCommit')
foreach($p in $positionals) { if($known -contains $p) { $action = $p; break } }

$python = Get-Command python -ErrorAction SilentlyContinue
if($null -eq $python){ $python = Get-Command py -ErrorAction SilentlyContinue }
if($null -eq $python){ throw 'Canonical Havenwild source-control authority requires Python, but Python was not found.' }

function Get-ActiveGitBranch {
  $branch = (@(& git -C $root symbolic-ref --quiet --short HEAD 2>$null) -join '').Trim()
  if($LASTEXITCODE -ne 0) { return '' }
  return $branch
}

function Assert-ExperimentalGreen {
  $markerPath = Join-Path $root '.havenwild\last-green-quality-gate.json'
  if(-not (Test-Path -LiteralPath $markerPath -PathType Leaf)) {
    throw 'Experimental publication requires a GREEN Full Quality Gate marker.'
  }
  $marker = Get-Content -LiteralPath $markerPath -Raw | ConvertFrom-Json
  if([string]$marker.result -ne 'PASS') {
    throw 'Experimental publication requires a PASS Full Quality Gate marker.'
  }
  if([string]$marker.gitBranchAtGate -ne 'experimental') {
    throw ("Experimental publication requires a gate certified on experimental; marker branch is {0}." -f [string]$marker.gitBranchAtGate)
  }
}

function Invoke-ExperimentalReconcile {
  $reconcile = Join-Path $PSScriptRoot 'ReconcilePublishedLane.py'
  if(-not (Test-Path -LiteralPath $reconcile -PathType Leaf)) {
    throw "Experimental publication reconciliation authority is missing: $reconcile"
  }
  & $python.Source $reconcile '--root' $root '--branch' 'experimental'
  if($LASTEXITCODE -ne 0) {
    throw 'Experimental publication reached GitHub but reconciliation failed.'
  }
}

function Push-ExperimentalGreen {
  Assert-ExperimentalGreen
  # CommitGreen must have just bound this exact HEAD to the canonical marker.
  # Do not allow a standalone Push to publish a later manual/uncertified commit.
  $marker=(Get-Content -LiteralPath (Join-Path $root '.havenwild\last-green-quality-gate.json') -Raw | ConvertFrom-Json)
  $head=(@(& git -C $root rev-parse HEAD 2>$null) -join '').Trim()
  if($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($head) -or [string]$marker.committedCommit -ne $head){
    throw 'Experimental push blocked: HEAD is not the exact certified CommitGreen commit.'
  }
  # Status is an informational JSON endpoint and intentionally returns zero even
  # when gateState=STALE. Inspect its fields, not only the process exit code.
  $statusOutput = @(& $python.Source (Join-Path $PSScriptRoot 'HavenwildGateAuthority.py') 'git' '--root' $root '--action' 'Status')
  if($LASTEXITCODE -ne 0){ throw 'Experimental push blocked: canonical authority Status failed.' }
  try { $sourceStatus = (($statusOutput -join "`n") | ConvertFrom-Json -ErrorAction Stop) }
  catch { throw 'Experimental push blocked: canonical authority Status did not return valid JSON.' }
  if([string]$sourceStatus.gateState -ne 'GREEN' -or $sourceStatus.publicationEligible -ne $true){
    throw ("Experimental push blocked: canonical source certification is stale ({0}: {1})." -f [string]$sourceStatus.gateState,[string]$sourceStatus.blockReason)
  }
  & git -C $root diff --cached --quiet
  if($LASTEXITCODE -ne 0){ throw 'Experimental push blocked: unexpected staged changes remain after GREEN commit.' }
  & git -C $root push -u origin experimental
  if($LASTEXITCODE -ne 0) { throw 'Push to origin/experimental failed.' }
  & git -C $root fetch origin experimental
  if($LASTEXITCODE -ne 0) { throw 'Fetch of origin/experimental after push failed.' }
  $head = (@(& git -C $root rev-parse HEAD 2>$null) -join '').Trim()
  $remoteHead = (@(& git -C $root rev-parse refs/remotes/origin/experimental 2>$null) -join '').Trim()
  if([string]::IsNullOrWhiteSpace($head) -or $remoteHead -ne $head) {
    throw ("Experimental push did not reconcile to local HEAD (local={0}, remote={1})." -f $head,$remoteHead)
  }
  Invoke-ExperimentalReconcile
  Write-Host "PUSH PASS: origin/experimental = $head"
}

# CC8E16: Setup is no longer a blind git-init/fetch operation. A GitHub Download ZIP
# can already contain a valuable hydrated/validated working tree, so connect/repair
# adopts origin/main history with git reset --mixed while proving governed file bytes
# did not change. Divergent local history is backed up before adoption.
$normalizedAction = $action.Trim().ToLowerInvariant().Replace('-','').Replace('_','')
$currentBranch = Get-ActiveGitBranch
if($normalizedAction -in @('setup','init','initialize','connect','repair','adopt')) {
  if($currentBranch -eq 'experimental') {
    throw 'Repository repair/setup is Main-oriented and is blocked while Experimental is active. Switch deliberately before running repository adoption/repair.'
  }
  $repair = Join-Path $PSScriptRoot 'RepairGitWorkingCopy.py'
  if(-not (Test-Path -LiteralPath $repair -PathType Leaf)) { throw "Git working-folder repair authority is missing: $repair" }
  $repairArgs = @($repair,'--root',$root)
  if(-not [string]::IsNullOrWhiteSpace($remote)) { $repairArgs += @('--remote',$remote) }
  & $python.Source @repairArgs
  exit $LASTEXITCODE
}

$authority = Join-Path $PSScriptRoot 'HavenwildGateAuthority.py'
if(-not (Test-Path -LiteralPath $authority)){ throw "Canonical Havenwild source-control authority is missing: $authority" }

# HW-EXPERIMENTAL-LANE-32: protected Experimental publication is branch-aware.
# The canonical GREEN authority still owns certification/staging/commit. This bridge
# owns only the branch-specific push and reconciliation until the authority itself is
# generalized in the later source-control convergence pass. Main is never moved here.
if($currentBranch -eq 'experimental') {
  if($normalizedAction -eq 'commitpushgreen') {
    Assert-ExperimentalGreen
    $commitArgs = @($authority,'git','--root',$root,'--action','CommitGreen')
    if(-not [string]::IsNullOrWhiteSpace($message)){ $commitArgs += @('--message',$message) }
    if(-not [string]::IsNullOrWhiteSpace($remote)){ $commitArgs += @('--remote',$remote) }
    & $python.Source @commitArgs
    if($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Push-ExperimentalGreen
    exit 0
  }
  if($normalizedAction -in @('push','pushmain')) {
    Push-ExperimentalGreen
    exit 0
  }
  if($normalizedAction -eq 'pull') {
    & git -C $root pull --ff-only origin experimental
    if($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host 'PULL PASS: origin/experimental fast-forward only'
    exit 0
  }
}

# HW-PCC-RETIRED-TRACKED-CLEANUP-01:
# updates/inbox is now deliberately excluded from governed source, but older
# repository history still contains tracked checksum sidecars there. When a
# certified GREEN commit is published, stage ONLY already-tracked deletions
# beneath this explicitly retired prefix. This lets the PCC finish the one-time
# retirement without widening governed source or sweeping arbitrary ignored
# files into a protected commit.
if($normalizedAction -in @('commitgreen','commitpushgreen')) {
  $retiredPrefix = 'updates/inbox'
  $retiredDeleted = @(& git -C $root ls-files --deleted -- $retiredPrefix)
  if($LASTEXITCODE -ne 0) {
    throw 'Unable to inspect retired tracked paths under updates/inbox.'
  }

  $retiredDeleted = @(
    $retiredDeleted | Where-Object {
      $candidate = ([string]$_).Replace('\','/').Trim()
      -not [string]::IsNullOrWhiteSpace($candidate) -and
      $candidate.ToLowerInvariant().StartsWith('updates/inbox/')
    }
  )

  if($retiredDeleted.Count -gt 0) {
    & git -C $root add -u -- @retiredDeleted
    if($LASTEXITCODE -ne 0) {
      throw 'Unable to stage retired tracked deletions under updates/inbox.'
    }
    Write-Host "RETIRED TRACKED CLEANUP: staged $($retiredDeleted.Count) deletion(s) under updates/inbox/"
  }
}

$callArgs = @($authority,'git','--root',$root,'--action',$action)
if(-not [string]::IsNullOrWhiteSpace($message)){ $callArgs += @('--message',$message) }
if(-not [string]::IsNullOrWhiteSpace($remote)){ $callArgs += @('--remote',$remote) }
& $python.Source @callArgs
$authorityExit = $LASTEXITCODE

# Main retains the historical strict protected-publication reconciliation.
if($authorityExit -ne 0 -and $normalizedAction -in @('commitpushgreen','push','pushmain')) {
  $reconcile = Join-Path $PSScriptRoot 'ReconcilePublishedGreen.py'
  if(Test-Path -LiteralPath $reconcile -PathType Leaf) {
    Write-Host 'Protected publication returned non-zero; verifying governed-source reconciliation...'
    & $python.Source $reconcile '--root' $root
    if($LASTEXITCODE -eq 0) { exit 0 }
  }
}
exit $authorityExit
