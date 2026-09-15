[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$Root,
  [ValidateSet('Status','Toggle','SwitchExperimental','SwitchMain','MoveWorkToExperimental','CompareMain','PrepareCutover')]
  [string]$Action='Status'
)

$ErrorActionPreference='Stop'
$Root=(Resolve-Path -LiteralPath $Root).Path
$PolicyPath=Join-Path $Root 'content\architecture\havenwild_development_lane_policy_v1.json'
$StateRoot=Join-Path $Root '.havenwild'
$StatePath=Join-Path $StateRoot 'development-lane.json'
$CutoverPlanPath=Join-Path $StateRoot 'experimental-cutover-plan.json'

function Invoke-Git {
  param([Parameter(Mandatory=$true)][string[]]$Args,[switch]$AllowFailure)
  # PowerShell 5 may promote ordinary native stderr (for example Git fetch progress)
  # into NativeCommandError when the caller uses ErrorActionPreference=Stop.
  # Temporarily demote native stderr to normal captured output and trust Git's exit code.
  $oldPreference=$ErrorActionPreference
  try {
    $ErrorActionPreference='Continue'
    $output=@(& git -C $Root @Args 2>&1)
    $code=$LASTEXITCODE
  } finally {
    $ErrorActionPreference=$oldPreference
  }
  $text=(($output | ForEach-Object { [string]$_ }) -join "`n").Trim()
  if(-not $AllowFailure -and $code -ne 0) {
    throw ("git {0} failed ({1}): {2}" -f ($Args -join ' '),$code,$text)
  }
  return [pscustomobject]@{ Code=$code; Text=$text }
}

function Get-Policy {
  if(-not (Test-Path -LiteralPath $PolicyPath -PathType Leaf)) { throw "Development-lane policy is missing: $PolicyPath" }
  $policy=Get-Content -LiteralPath $PolicyPath -Raw | ConvertFrom-Json
  if([string]$policy.schema -ne 'havenwild.development_lane_policy.v1') { throw "Unsupported development-lane policy schema: $($policy.schema)" }
  return $policy
}

function Get-Branch {
  return (Invoke-Git -Args @('symbolic-ref','--quiet','--short','HEAD') -AllowFailure).Text
}

function Get-RefSha([string]$Ref) {
  $result=Invoke-Git -Args @('rev-parse','--verify',$Ref) -AllowFailure
  if($result.Code -ne 0 -or [string]::IsNullOrWhiteSpace($result.Text)) { return $null }
  return $result.Text.Trim()
}

function Get-PreferredBranchSha([string]$Branch) {
  $local=Get-RefSha ("refs/heads/{0}" -f $Branch)
  if($local) { return $local }
  return Get-RefSha ("refs/remotes/origin/{0}" -f $Branch)
}

function Get-WorkTreeState {
  $result=Invoke-Git -Args @('status','--porcelain=v1','--untracked-files=normal')
  if([string]::IsNullOrWhiteSpace($result.Text)) { return 'Clean' }
  return 'Modified'
}

function Test-IsAncestor([string]$Older,[string]$Newer) {
  if([string]::IsNullOrWhiteSpace($Older) -or [string]::IsNullOrWhiteSpace($Newer)) { return $false }
  $result=Invoke-Git -Args @('merge-base','--is-ancestor',$Older,$Newer) -AllowFailure
  return ($result.Code -eq 0)
}

function Get-AheadBehind([string]$Stable,[string]$Development) {
  $stableSha=Get-PreferredBranchSha $Stable
  $devSha=Get-PreferredBranchSha $Development
  if(-not $stableSha -or -not $devSha) { return [pscustomobject]@{ Ahead=$null; Behind=$null } }
  $result=Invoke-Git -Args @('rev-list','--left-right','--count',("$stableSha...$devSha")) -AllowFailure
  if($result.Code -eq 0 -and $result.Text -match '^\s*(\d+)\s+(\d+)\s*$') {
    return [pscustomobject]@{ Behind=[int]$Matches[1]; Ahead=[int]$Matches[2] }
  }
  return [pscustomobject]@{ Ahead=$null; Behind=$null }
}

function Get-ExperimentalGateState {
  $marker=Join-Path $StateRoot 'last-green-quality-gate.json'
  if(-not (Test-Path -LiteralPath $marker -PathType Leaf)) { return 'NONE' }
  try {
    $gate=Get-Content -LiteralPath $marker -Raw | ConvertFrom-Json
    if([string]$gate.result -ne 'PASS') { return 'STALE' }
    if([string]$gate.gitBranchAtGate -eq 'experimental') { return 'GREEN' }
    return 'OTHER-LANE'
  } catch { return 'UNREADABLE' }
}

function Write-LaneState([object]$Policy) {
  New-Item -ItemType Directory -Force -Path $StateRoot | Out-Null
  $branch=Get-Branch
  $stable=[string]$Policy.stableBranch
  $development=[string]$Policy.developmentBranch
  $ab=Get-AheadBehind $stable $development
  $payload=[ordered]@{
    schema='havenwild.development_lane_state.v1'
    updatedUtc=(Get-Date).ToUniversalTime().ToString('o')
    activeBranch=$branch
    activeLane=$(if($branch -eq $development){'experimental'}elseif($branch -eq $stable){'main'}else{'other'})
    stableBranch=$stable
    developmentBranch=$development
    stableSha=Get-PreferredBranchSha $stable
    developmentSha=Get-PreferredBranchSha $development
    experimentalParentGreenCommit=[string]$Policy.experimentalParentGreenCommit
    experimentalAhead=$ab.Ahead
    experimentalBehind=$ab.Behind
    workTree=Get-WorkTreeState
    experimentalGate=Get-ExperimentalGateState
    cutoverAuthorized=$false
  }
  $payload | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $StatePath -Encoding UTF8
  return [pscustomobject]$payload
}

function Show-Status([object]$Policy) {
  $state=Write-LaneState $Policy
  Write-Host 'HAVENWILD DEVELOPMENT LANE'
  Write-Host (" Active lane  : {0}" -f ([string]$state.activeLane).ToUpperInvariant())
  Write-Host (" Branch       : {0}" -f $state.activeBranch)
  Write-Host (" Work tree    : {0}" -f $state.workTree)
  Write-Host (" Main         : {0}" -f $(if($state.stableSha){$state.stableSha}else{'<missing>'}))
  Write-Host (" Experimental : {0}" -f $(if($state.developmentSha){$state.developmentSha}else{'<missing>'}))
  Write-Host (" Ahead main   : {0}" -f $(if($null -ne $state.experimentalAhead){$state.experimentalAhead}else{'<unknown>'}))
  Write-Host (" Behind main  : {0}" -f $(if($null -ne $state.experimentalBehind){$state.experimentalBehind}else{'<unknown>'}))
  Write-Host (" Exp. gate    : {0}" -f $state.experimentalGate)
  Write-Host ' Cutover      : LOCKED - explicit user authorization required'
}

function Sync-ExperimentalBootstrap([object]$Policy) {
  $stable=[string]$Policy.stableBranch
  $development=[string]$Policy.developmentBranch
  $stableSha=Get-RefSha ("refs/heads/{0}" -f $stable)
  if(-not $stableSha) { throw "Stable branch '$stable' is unavailable locally." }

  # Refresh tracking refs when possible, but remote network/auth failure must not
  # invalidate a perfectly usable local certified bootstrap.
  $null=Invoke-Git -Args @('fetch','origin',$stable,$development) -AllowFailure

  $devLocal=Get-RefSha ("refs/heads/{0}" -f $development)
  $devRemote=Get-RefSha ("refs/remotes/origin/{0}" -f $development)
  $devSha=$(if($devLocal){$devLocal}else{$devRemote})

  if(-not $devSha) {
    Invoke-Git -Args @('branch',$development,$stableSha) | Out-Null
    Write-Host "Created local '$development' from certified '$stable' baseline $stableSha."
    return
  }

  if($devSha -eq $stableSha) {
    if(-not $devLocal) { Invoke-Git -Args @('branch',$development,$stableSha) | Out-Null }
    return
  }

  if(Test-IsAncestor $devSha $stableSha) {
    # Experimental is strictly behind Main. This is the one allowed automatic
    # bootstrap direction: move only the local Experimental ref forward to Main.
    if($devLocal) { Invoke-Git -Args @('branch','-f',$development,$stableSha) | Out-Null }
    else { Invoke-Git -Args @('branch',$development,$stableSha) | Out-Null }
    Write-Host "Fast-forwarded local '$development' to certified '$stable' baseline $stableSha."
    return
  }

  if(Test-IsAncestor $stableSha $devSha) {
    # Experimental is already ahead of Main. Keep it exactly as-is.
    if(-not $devLocal) { Invoke-Git -Args @('branch',$development,$devSha) | Out-Null }
    return
  }

  throw "Main and Experimental have diverged. Automatic lane bootstrap is blocked; review/compare is required."
}

function Switch-Experimental([object]$Policy) {
  if((Get-WorkTreeState) -ne 'Clean') { throw 'Switch to Experimental is blocked because the working tree is modified.' }
  $development=[string]$Policy.developmentBranch
  Sync-ExperimentalBootstrap $Policy
  Invoke-Git -Args @('switch',$development) | Out-Null
  $remote=Get-RefSha ("refs/remotes/origin/{0}" -f $development)
  if($remote) { $null=Invoke-Git -Args @('branch','--set-upstream-to',("origin/{0}" -f $development),$development) -AllowFailure }
  Write-Host "Experimental lane active on branch '$development'."
  Show-Status $Policy
}

function Switch-Main([object]$Policy) {
  if((Get-WorkTreeState) -ne 'Clean') { throw 'Switch to Main is blocked because the working tree is modified. Commit/stash Experimental work first.' }
  $stable=[string]$Policy.stableBranch
  if(-not (Get-PreferredBranchSha $stable)) { throw "Stable branch '$stable' is unavailable." }
  Invoke-Git -Args @('switch',$stable) | Out-Null
  Write-Host "Main inspection lane active on branch '$stable'. Routine development publication remains protected."
  Show-Status $Policy
}

function Move-WorkToExperimental([object]$Policy) {
  $current=Get-Branch
  $development=[string]$Policy.developmentBranch
  $stable=[string]$Policy.stableBranch
  if($current -eq $development) { Write-Host 'Experimental is already active; current working changes are already on the development lane.'; Show-Status $Policy; return }
  if($current -ne $stable) { throw "Automatic work transfer is supported only from '$stable' to '$development'; current branch is '$current'." }

  $dirty=((Get-WorkTreeState) -ne 'Clean')
  $stashRefBefore=Get-RefSha 'refs/stash'
  $stashCreated=$false
  if($dirty) {
    $label='havenwild-pcc-lane-transfer-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
    $null=Invoke-Git -Args @('stash','push','-u','-m',$label)
    $stashRefAfter=Get-RefSha 'refs/stash'
    $stashCreated=($stashRefAfter -and $stashRefAfter -ne $stashRefBefore)
    if(-not $stashCreated) { throw 'Working tree was modified but Git did not create a transfer stash.' }
    Write-Host "Preserved current Main working changes in temporary stash: $label"
  }

  try { Switch-Experimental $Policy }
  catch {
    if($stashCreated) {
      try { Invoke-Git -Args @('switch',$stable) | Out-Null } catch {}
      try { $null=Invoke-Git -Args @('stash','pop') -AllowFailure } catch {}
    }
    throw
  }

  if($stashCreated) {
    $restore=Invoke-Git -Args @('stash','pop') -AllowFailure
    if($restore.Code -ne 0) { throw 'Experimental is active, but restoring the preserved work reported conflicts. Git retained the stash; resolve conflicts before continuing.' }
    Write-Host 'Restored preserved working changes onto Experimental.'
  }
  Show-Status $Policy
}

function Toggle-Lane([object]$Policy) {
  $branch=Get-Branch
  $stable=[string]$Policy.stableBranch
  $development=[string]$Policy.developmentBranch
  if($branch -eq $stable) {
    if((Get-WorkTreeState) -eq 'Clean') { Switch-Experimental $Policy } else { Move-WorkToExperimental $Policy }
    return
  }
  if($branch -eq $development) { Switch-Main $Policy; return }
  throw "Lane toggle supports only '$stable' and '$development'; current branch is '$branch'."
}

function Compare-Main([object]$Policy) {
  $stable=[string]$Policy.stableBranch
  $development=[string]$Policy.developmentBranch
  $ab=Get-AheadBehind $stable $development
  Write-Host 'EXPERIMENTAL -> MAIN COMPARISON'
  Write-Host (" Ahead  : {0}" -f $(if($null -ne $ab.Ahead){$ab.Ahead}else{'<unknown>'}))
  Write-Host (" Behind : {0}" -f $(if($null -ne $ab.Behind){$ab.Behind}else{'<unknown>'}))
  $stat=Invoke-Git -Args @('diff','--stat',("$stable...$development")) -AllowFailure
  if(-not [string]::IsNullOrWhiteSpace($stat.Text)) { Write-Host $stat.Text }
}

function Prepare-Cutover([object]$Policy) {
  $development=[string]$Policy.developmentBranch
  if((Get-Branch) -ne $development) { throw "Cutover preparation must run from '$development'." }
  if((Get-WorkTreeState) -ne 'Clean') { throw 'Cutover preparation requires a clean Experimental working tree.' }
  $gatePath=Join-Path $StateRoot 'last-green-quality-gate.json'
  if(-not (Test-Path -LiteralPath $gatePath -PathType Leaf)) { throw 'Cutover preparation requires a GREEN Experimental Full Quality Gate.' }
  $gate=Get-Content -LiteralPath $gatePath -Raw | ConvertFrom-Json
  if([string]$gate.result -ne 'PASS' -or [string]$gate.gitBranchAtGate -ne $development) { throw 'Latest GREEN gate does not certify the Experimental branch.' }
  $stable=[string]$Policy.stableBranch
  $mainSha=Get-PreferredBranchSha $stable
  $experimentalSha=Get-PreferredBranchSha $development
  if(-not $mainSha -or -not $experimentalSha) { throw 'Unable to resolve Main/Experimental SHAs.' }
  if(-not (Test-IsAncestor $mainSha $experimentalSha)) { throw 'Main is not an ancestor of Experimental; cutover requires review before any merge.' }
  New-Item -ItemType Directory -Force -Path $StateRoot | Out-Null
  [ordered]@{
    schema='havenwild.experimental_cutover_plan.v1'
    createdUtc=(Get-Date).ToUniversalTime().ToString('o')
    stableBranch=$stable
    stableSha=$mainSha
    developmentBranch=$development
    developmentSha=$experimentalSha
    greenGateRunId=[string]$gate.runId
    authorized=$false
    nextStep='Explicit user authorization is required before any Main branch mutation.'
  } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $CutoverPlanPath -Encoding UTF8
  Write-Host "CUTOVER PLAN READY: $CutoverPlanPath"
  Write-Host 'No branch was changed. Cutover remains LOCKED.'
}

if(-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'Development lanes require Git on PATH.' }
$probe=Invoke-Git -Args @('rev-parse','--is-inside-work-tree') -AllowFailure
if($probe.Code -ne 0 -or $probe.Text.Trim().ToLowerInvariant() -ne 'true') { throw 'Havenwild development-lane authority requires a Git working tree.' }

$policy=Get-Policy
switch($Action) {
  'Status' { Show-Status $policy }
  'Toggle' { Toggle-Lane $policy }
  'SwitchExperimental' { Switch-Experimental $policy }
  'SwitchMain' { Switch-Main $policy }
  'MoveWorkToExperimental' { Move-WorkToExperimental $policy }
  'CompareMain' { Compare-Main $policy }
  'PrepareCutover' { Prepare-Cutover $policy }
}
