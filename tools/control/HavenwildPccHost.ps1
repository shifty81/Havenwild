[CmdletBinding()]
param(
  [string]$Command='menu',
  [string]$Pass='manual',
  [switch]$ReturnToMenu,
  [string]$RestartToken=''
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version 2.0
$Root=(Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
. (Join-Path $PSScriptRoot 'PccRestartTicket.ps1')
. (Join-Path $PSScriptRoot 'PccJobHost.ps1')
. (Join-Path $PSScriptRoot 'PccPatchLedger.ps1')
. (Join-Path $PSScriptRoot 'PccPatchPreflight.ps1')
. (Join-Path $PSScriptRoot 'PccCommandHost.ps1')
. (Join-Path $PSScriptRoot 'PccRootHandoffClassifier.ps1')

function Get-PccControlFingerprint {
  $rows=@()
  foreach($relative in @(
    'HavenwildTools.cmd','tools\control\HavenwildPccHost.ps1','tools\control\PccRestartTicket.ps1',
    'tools\control\PccJobHost.ps1','tools\control\PccPatchLedger.ps1','tools\control\PccPatchPreflight.ps1',
    'tools\control\PccCommandHost.ps1','tools\control\PccCommandExtensions.ps1','tools\control\PccQuickState.py','tools\control\HavenwildTools.ps1',
    'tools\control\ProjectCommandRegistry.ps1','tools\control\InvokeRootPatchIntake.ps1','tools\control\DevelopmentLane.ps1',
    'tools\control\PccRootHandoffClassifier.ps1','tools\control\PccVaultAdapter.py'
  )){
    $path=Join-Path $Root $relative
    if(Test-Path -LiteralPath $path -PathType Leaf){ $rows += ("$relative|" + (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()) }
    else { $rows += "$relative|missing" }
  }
  $sha=[Security.Cryptography.SHA256]::Create()
  try { return ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes(($rows -join "`n"))))).Replace('-','').ToLowerInvariant() }
  finally { $sha.Dispose() }
}

function Get-PccQuickState {
  $python=Get-Command python -ErrorAction SilentlyContinue
  if($null -eq $python){ $python=Get-Command py -ErrorAction SilentlyContinue }
  if($null -eq $python){ return $null }
  $raw=@(& $python.Source (Join-Path $PSScriptRoot 'PccQuickState.py') '--root' $Root 2>$null)
  if($LASTEXITCODE -ne 0 -or $raw.Count -eq 0){ return $null }
  try { return (($raw -join "`n") | ConvertFrom-Json) } catch { return $null }
}

function Show-PccHeader {
  Clear-Host
  $s=Get-PccQuickState
  Write-Host '========================================================================' -ForegroundColor DarkCyan
  Write-Host ' HAVENWILD PROJECT CONTROL CENTER v2' -ForegroundColor Cyan
  Write-Host '========================================================================' -ForegroundColor DarkCyan
  Write-Host (" Repository : {0}" -f $Root)
  if($null -ne $s){
    $lane=if([string]$s.lane -eq 'experimental'){'EXPERIMENTAL'}elseif([string]$s.lane -eq 'main'){'MAIN / PROTECTED'}else{[string]$s.lane}
    Write-Host (" Lane       : {0} ({1})" -f $lane,[string]$s.branch) -ForegroundColor $(if([string]$s.lane -eq 'experimental'){'Cyan'}else{'Yellow'})
    Write-Host (" Git        : {0}" -f [string]$s.gitState)
    Write-Host (" Local      : {0}" -f [string]$s.localPatch)
    Write-Host (" Repository : {0}" -f [string]$s.repositoryPatch)
    Write-Host (" Sync       : {0}" -f [string]$s.syncState)
    Write-Host (" Gate       : {0}" -f [string]$s.gateState)
  }
  $patches=@(Get-PccPendingPatchFiles -Root $Root)
  Write-Host (" Updates    : {0} pending" -f $patches.Count)
  $job=Get-PccLatestJob -Root $Root
  if($null -ne $job){ Write-Host (" Last job   : {0} [{1}] {2:N1}s" -f [string]$job.name,[string]$job.result,[double]$job.durationSeconds) }
  Write-Host '------------------------------------------------------------------------' -ForegroundColor DarkCyan
}

function Invoke-PccPatchIntake {
  param(
    [switch]$Prompt,
    [string]$ResumeCommand='menu',
    [switch]$ReturnToMenuAfterRestart
  )
  $null=Move-PccRootHandoffArtifacts -Root $Root
  $patches=@(Get-PccPendingPatchFiles -Root $Root)
  if($patches.Count -eq 0){ return 0 }
  $preflight=Invoke-PccPatchLanePreflight -Root $Root -Patches $patches
  # Snapshot patch metadata before invoking root intake. Intake is allowed to move
  # transports into applied/failed archives, so post-apply bookkeeping must never
  # reopen stale FileInfo paths from the original discovery snapshot.
  $patchRecords=@()
  foreach($p in $patches){
    $t=Get-PccPatchTarget -Patch $p
    $patchRecords += [pscustomobject]@{
      Name=[string]$p.Name
      FullName=[string]$p.FullName
      TargetLane=[string]$t.Lane
      Required=[bool]$t.Required
    }
    Write-PccPatchLedgerEntry -Root $Root -Transport $p.Name -Status 'PENDING' -TargetLane $t.Lane -Required $t.Required -Message 'Discovered by PCC v2 preflight.'
  }
  $before=Get-PccControlFingerprint
  $intakeStartedUtc=(Get-Date).ToUniversalTime()
  $intake=Join-Path $Root 'tools\control\InvokeRootPatchIntake.ps1'
  $args=@('-NoProfile','-ExecutionPolicy','Bypass','-File',$intake,'-Root',$Root)
  if($Prompt){ $args += '-Prompt' }
  & powershell @args
  $rc=$LASTEXITCODE
  foreach($record in $patchRecords){
    $evidence=Get-PccPatchArchiveEvidence -Root $Root -Transport $record.Name -SinceUtc $intakeStartedUtc
    if($null -ne $evidence -and [string]$evidence.Status -eq 'FAILED'){
      Write-PccPatchLedgerEntry -Root $Root -Transport $record.Name -Status 'FAILED' -TargetLane $record.TargetLane -Required $record.Required -Message ("Legacy intake archived transport as failed: {0}" -f [string]$evidence.Path)
    } elseif($null -ne $evidence -and [string]$evidence.Status -eq 'APPLIED'){
      Write-PccPatchLedgerEntry -Root $Root -Transport $record.Name -Status 'APPLIED' -TargetLane $record.TargetLane -Required $record.Required -Message ("Applied archive evidence: {0}" -f [string]$evidence.Path)
    } elseif(Test-Path -LiteralPath $record.FullName -PathType Leaf){
      Write-PccPatchLedgerEntry -Root $Root -Transport $record.Name -Status 'DEFERRED' -TargetLane $record.TargetLane -Required $record.Required -Message 'Transport remains in root after intake.'
    } elseif($rc -ne 0){
      Write-PccPatchLedgerEntry -Root $Root -Transport $record.Name -Status 'FAILED' -TargetLane $record.TargetLane -Required $record.Required -Message ("Root intake exited with code {0}." -f $rc)
    } else {
      Write-PccPatchLedgerEntry -Root $Root -Transport $record.Name -Status 'FAILED' -TargetLane $record.TargetLane -Required $record.Required -Message 'Transport disappeared without APPLIED archive evidence; fail closed.'
    }
  }
  if($rc -ne 0){ return $rc }
  $after=Get-PccControlFingerprint
  if($after -ne $before){
    Write-Host 'PCC source changed during patch intake; performing one-shot replacement restart.' -ForegroundColor Yellow
    $replacement=Start-PccReplacement -Root $Root -Reason 'control-center-update' -ResumeCommand $ResumeCommand -Pass $Pass -ReturnToMenu:$ReturnToMenuAfterRestart -WaitForCompletion:(-not $ReturnToMenuAfterRestart)
    exit ([int]$replacement.ExitCode)
  }
  if([bool]$preflight.Switched){
    Write-Host 'Development lane changed during patch preflight; reloading the PCC once on the active lane.' -ForegroundColor Yellow
    $replacement=Start-PccReplacement -Root $Root -Reason 'lane-preflight-switch' -ResumeCommand $ResumeCommand -Pass $Pass -ReturnToMenu:$ReturnToMenuAfterRestart -WaitForCompletion:(-not $ReturnToMenuAfterRestart)
    exit ([int]$replacement.ExitCode)
  }
  return 0
}

function Assert-PccGateReady {
  $blocking=@(Get-PccBlockingPatchFailures -Root $Root)
  if($blocking.Count -gt 0){
    Write-Host 'FULL GATE BLOCKED: a required patch is in FAILED state.' -ForegroundColor Red
    foreach($b in $blocking){ Write-Host (" - {0}: {1}" -f [string]$b.transport,[string]$b.message) -ForegroundColor Yellow }
    return $false
  }
  $python=Get-Command python -ErrorAction SilentlyContinue
  if($null -eq $python){ $python=Get-Command py -ErrorAction SilentlyContinue }
  if($null -eq $python){ Write-Host 'PCC v2 validation requires Python.' -ForegroundColor Red; return $false }
  & $python.Source (Join-Path $Root 'tools\validation\Validate-HavenwildPccV2.py') '--root' $Root
  return ($LASTEXITCODE -eq 0)
}

function Invoke-PccGate {
  param([ValidateSet('full','fast')][string]$Mode)
  $key=if($Mode -eq 'full'){'validation.full-quality-gate'}else{'validation.fast-quality-gate'}
  $returnMenu=($Command -eq 'menu' -or [bool]$ReturnToMenu)
  $rc=Invoke-PccPatchIntake -ResumeCommand $key -ReturnToMenuAfterRestart:$returnMenu
  if($rc -ne 0){ return $rc }
  if(-not (Assert-PccGateReady)){ return 2 }
  $gateRc=Invoke-PccJob -Root $Root -Name ("{0} quality gate" -f $Mode) -CommandKey $key -Action { $code=Invoke-PccLegacyCommand -Root $Root -Key $key -Pass $Pass; $global:LASTEXITCODE=$code }
  if($gateRc -eq 0 -and $Mode -eq 'full'){
    $python=Get-Command python -ErrorAction SilentlyContinue
    if($null -eq $python){ $python=Get-Command py -ErrorAction SilentlyContinue }
    if($null -ne $python){
      & $python.Source (Join-Path $Root 'tools\control\PccQuickState.py') '--root' $Root '--record-certification' *> $null
    }
  }
  return $gateRc
}

function Invoke-PccPublish {
  $markerPath=Join-Path $Root '.havenwild\last-green-quality-gate.json'
  if(-not (Test-Path -LiteralPath $markerPath -PathType Leaf)){ Write-Host 'No GREEN gate marker exists.' -ForegroundColor Red; return 2 }
  try { $marker=Get-Content -LiteralPath $markerPath -Raw | ConvertFrom-Json } catch { Write-Host 'GREEN marker is unreadable.' -ForegroundColor Red; return 2 }
  $message=("Havenwild {0} - certified GREEN" -f [string]$marker.pass)
  $helper=Join-Path $Root 'tools\control\GitSourceControl.ps1'
  return Invoke-PccJob -Root $Root -Name 'Commit + push current GREEN' -CommandKey 'source-control.commit-push-green' -Action {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $helper -Root $Root -Action CommitPushGreen -RemoteUrl 'https://github.com/shifty81/Havenwild.git' -Message $message
  }
}

function Invoke-PccLaneToggle {
  param([switch]$RestartInteractive)
  $lane=Join-Path $Root 'tools\control\DevelopmentLane.ps1'
  $rc=Invoke-PccJob -Root $Root -Name 'Toggle development lane' -CommandKey 'project.lane.toggle' -Action {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $lane -Root $Root -Action Toggle
  }
  if($rc -eq 0 -and $RestartInteractive){
    $null=Start-PccReplacement -Root $Root -Reason 'manual-lane-switch' -ResumeCommand 'menu' -Pass $Pass -ReturnToMenu
    exit 0
  }
  return $rc
}

function Invoke-PccRegistryMenu {
  param([string]$Menu,[string]$Title)
  $commands=@(Get-PccCommandRegistry -Root $Root | Where-Object { @($_.Menu) -contains $Menu } | Sort-Object @{Expression={if($null -ne $_.MenuOrder){[int]$_.MenuOrder}else{9999}}},Label)
  while($true){
    Show-PccHeader
    Write-Host (" {0}" -f $Title.ToUpperInvariant()) -ForegroundColor Cyan
    for($i=0;$i -lt $commands.Count;$i++){ Write-Host (" {0,2}. {1}" -f ($i+1),[string]$commands[$i].Label) }
    Write-Host '  0. Back' -ForegroundColor DarkGray
    $choice=Read-Host 'Select an option'
    if([string]::IsNullOrWhiteSpace($choice)){ return }
    if($choice -eq '0'){ return }
    $n=0
    if([int]::TryParse($choice,[ref]$n) -and $n -ge 1 -and $n -le $commands.Count){
      $entry=$commands[$n-1]
      $key=[string]$entry.Key
      $rc=Invoke-PccJob -Root $Root -Name ([string]$entry.Label) -CommandKey $key -Action {
        $code=Invoke-PccCommandKey -Root $Root -Key $key -Pass $Pass
        $global:LASTEXITCODE=$code
      }
      Write-Host ''; Read-Host 'Press Enter to return to the menu' | Out-Null
    } else { Write-Host 'Unknown menu option.' -ForegroundColor Yellow }
  }
}

function Invoke-PccSourceControlMenu {
  while($true){
    Show-PccHeader
    Write-Host ' SOURCE CONTROL & DEVELOPMENT LANES' -ForegroundColor Cyan
    Write-Host '  1. Git / GREEN status'
    Write-Host '  2. Commit + push current GREEN'
    Write-Host '  3. Development lane status'
    Write-Host '  4. Toggle Main / Experimental'
    Write-Host '  5. Compare Experimental -> Main'
    Write-Host '  6. Prepare Main cutover plan (NO MERGE)'
    Write-Host '  0. Back' -ForegroundColor DarkGray
    $choice=Read-Host 'Select an option'
    if([string]::IsNullOrWhiteSpace($choice)){ return }
    switch($choice){
      '0' { return }
      '1' { & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root 'tools\control\GitSourceControl.ps1') -Root $Root -Action Status }
      '2' { $null=Invoke-PccPublish }
      '3' { & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root 'tools\control\DevelopmentLane.ps1') -Root $Root -Action Status }
      '4' { $null=Invoke-PccLaneToggle -RestartInteractive }
      '5' { & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root 'tools\control\DevelopmentLane.ps1') -Root $Root -Action CompareMain }
      '6' { & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root 'tools\control\DevelopmentLane.ps1') -Root $Root -Action PrepareCutover }
      default { Write-Host 'Unknown menu option.' -ForegroundColor Yellow }
    }
    Write-Host ''; Read-Host 'Press Enter to return to the menu' | Out-Null
  }
}

$consumed=Consume-PccRestartTicket -Root $Root -Token $RestartToken
$skipStartupIntake=($null -ne $consumed)

# Preserve CLI compatibility for ForgePY and project-local automation.
if($Command -ne 'menu'){
  $commandRc=0
  if($Command -eq 'validation.full-quality-gate'){ $commandRc=Invoke-PccGate -Mode full }
  elseif($Command -eq 'validation.fast-quality-gate'){ $commandRc=Invoke-PccGate -Mode fast }
  elseif($Command -eq 'source-control.commit-push-green'){ $commandRc=Invoke-PccPublish }
  elseif($Command -eq 'project.lane.toggle'){ $commandRc=Invoke-PccLaneToggle }
  elseif(Test-PccCommandKey -Root $Root -Key $Command){ $commandRc=Invoke-PccCommandKey -Root $Root -Key $Command -Pass $Pass }
  else {
    Write-Host ("Unknown command key: {0}" -f $Command) -ForegroundColor Yellow
    $commandRc=2
  }
  if(-not [bool]$ReturnToMenu){ exit $commandRc }
  if($commandRc -ne 0){ Write-Host ("Command completed with code {0}; returning to interactive PCC by request." -f $commandRc) -ForegroundColor Yellow }
  $Command='menu'
}

if(-not $skipStartupIntake){
  $null=Move-PccRootHandoffArtifacts -Root $Root
  $patches=@(Get-PccPendingPatchFiles -Root $Root)
  if($patches.Count -gt 0){
    Show-PccHeader
    Write-Host ("STARTUP PATCH SCAN: {0} pending transport(s)." -f $patches.Count) -ForegroundColor Yellow
    $answer=Read-Host 'Run governed patch intake now? [Y/n]'
    if($answer -notmatch '^[Nn]'){ $null=Invoke-PccPatchIntake -Prompt -ResumeCommand 'menu' -ReturnToMenuAfterRestart }
  }
}

while($true){
  Show-PccHeader
  Write-Host '  1. FULL QUALITY GATE / CERTIFY GREEN' -ForegroundColor Green
  Write-Host '  2. COMMIT + PUSH CURRENT GREEN' -ForegroundColor Green
  Write-Host ''
  Write-Host '  3. Build & verify'
  Write-Host '  4. Run & play'
  Write-Host '  5. World, terrain & scene tools'
  Write-Host '  6. Asset authority & catalog'
  Write-Host '  7. Project maintenance & diagnostics'
  Write-Host '  8. Packaging & baselines'
  Write-Host '  9. Logs & help'
  Write-Host ' 10. Advanced / all registered commands' -ForegroundColor DarkGray
  Write-Host ' 11. Source control & development lanes'
  Write-Host ' 12. TOGGLE DEVELOPMENT LANE' -ForegroundColor Cyan
  Write-Host '  0. Exit' -ForegroundColor DarkGray
  $choice=Read-Host 'Select an option'
  # EOF / detached child must exit, never spin redrawing the menu.
  if([string]::IsNullOrWhiteSpace($choice)){ break }
  switch($choice){
    '0' { exit 0 }
    '1' { $null=Invoke-PccGate -Mode full; Write-Host ''; Read-Host 'Press Enter to return to the menu' | Out-Null }
    '2' { $null=Invoke-PccPublish; Write-Host ''; Read-Host 'Press Enter to return to the menu' | Out-Null }
    '3' { Invoke-PccRegistryMenu -Menu 'build' -Title 'Build & Verify' }
    '4' { Invoke-PccRegistryMenu -Menu 'run' -Title 'Run & Play' }
    '5' { Invoke-PccRegistryMenu -Menu 'world' -Title 'World, Terrain & Scene Tools' }
    '6' { Invoke-PccRegistryMenu -Menu 'assets' -Title 'Asset Authority & Catalog' }
    '7' { Invoke-PccRegistryMenu -Menu 'project' -Title 'Project Maintenance & Diagnostics' }
    '8' { Invoke-PccRegistryMenu -Menu 'package' -Title 'Packaging & Baselines' }
    '9' { Invoke-PccRegistryMenu -Menu 'logs' -Title 'Logs & Help' }
    '10' { Invoke-PccRegistryMenu -Menu 'advanced' -Title 'Advanced / All Registered Commands' }
    '11' { Invoke-PccSourceControlMenu }
    '12' { $null=Invoke-PccLaneToggle -RestartInteractive }
    default { Write-Host 'Unknown menu option.' -ForegroundColor Yellow; Start-Sleep -Milliseconds 500 }
  }
}
exit 0
