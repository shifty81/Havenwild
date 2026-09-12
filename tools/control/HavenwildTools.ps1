[CmdletBinding()]
param([string]$Command = "menu", [string]$Pass = "manual", [switch]$ReturnToMenu)
$ErrorActionPreference = "Continue"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$LogRoot = Join-Path $Root "logs"
$SessionRoot = Join-Path $LogRoot "sessions"
New-Item -ItemType Directory -Force -Path $SessionRoot | Out-Null
$SessionStamp = Get-Date -Format "yyyyMMdd-HHmmss"
$SessionLog = Join-Path $SessionRoot "havenwild-tools-$SessionStamp.log"
$script:LastName = "None"
$script:LastResult = "READY"
$script:LastDuration = "0.0s"
$script:LastActionExitCode = 0
$script:Commands = @(& (Join-Path $PSScriptRoot 'ProjectCommandRegistry.ps1'))
$script:StartupWarnings = @()
$packageTransportHelpers = @('APPLY_HAVENWILD_PATCH.cmd','APPLY_HAVENWILD_PATCH.md')
$script:GreenGateMarker = Join-Path $Root '.havenwild\last-green-quality-gate.json'
$script:GitRemoteUrl = 'https://github.com/shifty81/Havenwild.git'
$script:ArtifactIndexPath = Join-Path $Root '.havenwild\artifact-index.json'
$script:QualityGateActive = $false
$script:QualityGateRunId = $null
$script:QualityGateStarted = $null
$script:QualityGateActionLogs = @()
$script:QualityGateActions = @()
$script:CurrentCommandKey = $null
$script:LastDebugBundlePath = $null
$script:QualityGateHistoryRoot = Join-Path $Root '.havenwild\quality-gates'
$script:LatestQualityGatePath = Join-Path $Root '.havenwild\latest-quality-gate.json'
$script:FastGateHistoryRoot = Join-Path $Root '.havenwild\fast-gates'
$script:LatestFastGatePath = Join-Path $Root '.havenwild\latest-fast-gate.json'

# Cumulative patches may intentionally retire or relocate old source paths. Patch
# cleanup is housekeeping and must never prevent the project control center from
# opening.  A failed cleanup keeps its manifest/helper in place for an explicit
# retry and is surfaced as a startup warning instead of terminating the launcher.
$patchRemovalManifest = Join-Path $Root 'manifests\removals\PATCH_REMOVALS.txt'
if (Test-Path -LiteralPath $patchRemovalManifest) {
  $patchRemovalHelper = Join-Path $PSScriptRoot 'ApplyPatchRemovals.ps1'
  if (-not (Test-Path -LiteralPath $patchRemovalHelper -PathType Leaf)) {
    $message = "Patch cleanup helper is missing: $patchRemovalHelper. Cleanup was deferred."
    $script:StartupWarnings += $message
    Add-Content -Path $SessionLog -Value $message
  } else {
    try {
      & $patchRemovalHelper -Root $Root -Manifest $patchRemovalManifest
      Remove-Item -LiteralPath $patchRemovalManifest -Force -ErrorAction Stop
      foreach ($packageHelper in $packageTransportHelpers) {
        Remove-Item -LiteralPath (Join-Path $Root $packageHelper) -Force -ErrorAction SilentlyContinue
      }
      Add-Content -Path $SessionLog -Value 'Cumulative patch cleanup completed successfully.'
    } catch {
      $message = "Patch cleanup was deferred: $($_.Exception.Message)"
      $script:StartupWarnings += $message
      Add-Content -Path $SessionLog -Value $message
    }
  }
}

# Older cumulative transports placed two temporary helpers in the repository root.
# They are never source authority. Remove exact stale helper names even when an older
# package already consumed/lost its removal manifest so root-cleanliness validation
# cannot be blocked by transport residue.
foreach ($packageHelper in $packageTransportHelpers) {
  $packageHelperPath = Join-Path $Root $packageHelper
  if (Test-Path -LiteralPath $packageHelperPath -PathType Leaf) {
    try {
      Remove-Item -LiteralPath $packageHelperPath -Force -ErrorAction Stop
      Add-Content -Path $SessionLog -Value ("Removed stale cumulative-patch transport helper: {0}" -f $packageHelper)
    } catch {
      $message = "Could not remove stale cumulative-patch transport helper {0}: {1}" -f $packageHelper, $_.Exception.Message
      $script:StartupWarnings += $message
      Add-Content -Path $SessionLog -Value $message
    }
  }
}

function Write-Color([string]$Text,[ConsoleColor]$Color=[ConsoleColor]::Gray) {
  Write-Host $Text -ForegroundColor $Color
  Add-Content -Path $SessionLog -Value $Text
}
function Get-GitState {
  if (-not (Get-Command git -ErrorAction SilentlyContinue)) { return "Unavailable" }
  Push-Location $Root
  try { $s = git status --porcelain 2>$null; if ($LASTEXITCODE -ne 0) { return "Not a repository" }; if ($s) { return "Modified" } else { return "Clean" } }
  finally { Pop-Location }
}
function Test-GitRepository {
  if (-not (Get-Command git -ErrorAction SilentlyContinue)) { return $false }
  Push-Location $Root
  try {
    & git rev-parse --is-inside-work-tree *> $null
    return ($LASTEXITCODE -eq 0)
  } finally { Pop-Location }
}
function Get-GitStatusFingerprint {
  if(-not (Test-GitRepository)) { return $null }
  Push-Location $Root
  try {
    $status = (@(& git status --porcelain=v1 -uall 2>$null) -join "`n").TrimEnd()
    if($LASTEXITCODE -ne 0) { return $null }
    $bytes=[System.Text.Encoding]::UTF8.GetBytes($status)
    $sha=[System.Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-','').ToLowerInvariant() }
    finally { $sha.Dispose() }
  } finally { Pop-Location }
}
function Get-GovernedSourceContentFingerprint {
  # Certification is based on governed file bytes, not Git's tracked/untracked labels.
  # This remains stable across fetch/reset/upstream/bootstrap metadata changes.
  $rejectedPrefixes=@('.git/','.havenwild/','assets/','archive/','artifacts/','docs/archive/','docs/handoffs/','docs/legacy_project_docs/','docs/patch/','manifests/packages/','manifests/patches/','manifests/rollups/','manifests/handoffs/','manifests/recovery/','WORKSPACE/','logs/','Build/','target/','.local/')
  $rejectedExtensions=@('.png','.jpg','.jpeg','.webp','.gif','.bmp','.tga','.dds','.wav','.ogg','.mp3','.flac','.glb','.gltf','.fbx','.obj','.blend','.ttf','.otf','.woff','.woff2','.ase','.aseprite','.psd','.kra','.gz','.zip','.pyc','.pyo')
  $entries=New-Object System.Collections.Generic.List[string]
  $files=Get-ChildItem -LiteralPath $Root -Recurse -File -Force -ErrorAction SilentlyContinue | Sort-Object FullName
  foreach($file in $files) {
    $relative=$file.FullName.Substring($Root.Length).TrimStart([char[]]'\\/').Replace('\\','/')
    $skip=$false
    foreach($prefix in $rejectedPrefixes) {
      if($relative.StartsWith($prefix,[System.StringComparison]::OrdinalIgnoreCase)) { $skip=$true; break }
    }
    if($skip) { continue }
    $ext=[IO.Path]::GetExtension($relative).ToLowerInvariant()
    if($rejectedExtensions -contains $ext) { continue }
    if($relative -match '(^|/)__pycache__/') { continue }
    $hash=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    $entries.Add(('{0}`t{1}`t{2}' -f $relative,$file.Length,$hash))
  }
  $payload=($entries -join "`n")
  $sha=[System.Security.Cryptography.SHA256]::Create()
  try {
    $bytes=[System.Text.Encoding]::UTF8.GetBytes($payload)
    return [pscustomobject]@{ Fingerprint=([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-','').ToLowerInvariant(); Count=$entries.Count }
  } finally { $sha.Dispose() }
}

function Write-GreenGateMarker {
  try {
    $stateRoot=Split-Path -Parent $script:GreenGateMarker
    New-Item -ItemType Directory -Force -Path $stateRoot | Out-Null
    $gitReady=Test-GitRepository
    $head=$null
    if($gitReady) {
      Push-Location $Root
      try { $head=(@(& git rev-parse HEAD 2>$null) -join '').Trim(); if($LASTEXITCODE -ne 0){$head=$null} }
      finally { Pop-Location }
    }
    $marker=[ordered]@{
      schema='havenwild.green_quality_gate.v1'
      createdUtc=(Get-Date).ToUniversalTime().ToString('o')
      sessionLog=$SessionLog
      pass=Get-CurrentAcceptedPass
      runId=$script:QualityGateRunId
      gitReady=$gitReady
      gitHead=$head
      gitFingerprint=if($gitReady){Get-GitStatusFingerprint}else{$null}
      gitContentFingerprint=(Get-GovernedSourceContentFingerprint).Fingerprint
      gitContentFileCount=(Get-GovernedSourceContentFingerprint).Count
    }
    $marker | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $script:GreenGateMarker -Encoding UTF8
    Write-Color ("GREEN GATE MARKER: {0}" -f $script:GreenGateMarker) DarkGray
  } catch {
    Write-Color ("Green gate marker warning: {0}" -f $_.Exception.Message) Yellow
  }
}
function Invoke-GitSourceAction([string]$Action,[string]$Message='') {
  $helper=Join-Path $PSScriptRoot 'GitSourceControl.ps1'
  if(-not (Test-Path -LiteralPath $helper -PathType Leaf)) {
    Write-Color ("Git source-control helper is missing: {0}" -f $helper) Red
    return
  }
  # Never use $args/$Args here: PowerShell reserves $args as the automatic unbound-argument array.
  # A named dispatch vector guarantees -Action reaches GitSourceControl.ps1 from every menu route.
  $gitDispatchArgs=@('-Root',$Root,'-Action',$Action,'-RemoteUrl',$script:GitRemoteUrl)
  if(-not [string]::IsNullOrWhiteSpace($Message)) { $gitDispatchArgs += @('-Message',$Message) }
  Invoke-HavenwildAction ("GitHub: {0}" -f $Action) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $helper @gitDispatchArgs
  } 'source-control'
}
function Get-DefaultCommitMessage {
  $passLabel=if([string]::IsNullOrWhiteSpace($Pass) -or $Pass -eq 'manual'){'green checkpoint'}else{$Pass}
  return ("Havenwild {0} - verified {1}" -f $passLabel,(Get-Date -Format 'yyyy-MM-dd HH:mm'))
}
function Read-CommitMessage {
  $default=Get-DefaultCommitMessage
  $message=Read-Host ("Commit message [{0}]" -f $default)
  if([string]::IsNullOrWhiteSpace($message)){ return $default }
  return $message.Trim()
}
function Get-BuildState([string]$Exe) {
  foreach($p in @((Join-Path $Root "target\release\$Exe"),(Join-Path $Root "target\debug\$Exe"))){ if(Test-Path $p){ return "Ready" } }
  return "Missing"
}
function Get-BaselineState {
  $p=Join-Path $Root '.havenwild\package-baseline.json'
  if(Test-Path $p){ return 'Ready' }
  return 'Missing'
}
function Get-ControlCenterAuthorityFingerprint {
  $rows=@()
  foreach($relative in @(
    'tools\control\HavenwildTools.ps1',
    'tools\control\ProjectCommandRegistry.ps1',
    'tools\control\InvokeRootPatchIntake.ps1',
    'tools\control\PackageProject.ps1',
    'tools\control\CreateRecoveryRollup.ps1',
    'tools\control\RestoreLatestPatchBackup.ps1'
  )) {
    $path=Join-Path $Root $relative
    if(Test-Path -LiteralPath $path -PathType Leaf) {
      $rows += ("{0}|{1}" -f $relative,((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()))
    } else {
      $rows += ("{0}|missing" -f $relative)
    }
  }
  $text=$rows -join "`n"
  $bytes=[Text.Encoding]::UTF8.GetBytes($text)
  $sha=[Security.Cryptography.SHA256]::Create()
  try { return ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-','').ToLowerInvariant() }
  finally { $sha.Dispose() }
}
function Get-CommandById([string]$Id) {
  return $script:Commands | Where-Object { ([string]$_.Id -eq $Id) -or ([string]$_.Key -eq $Id) } | Select-Object -First 1
}
function Get-CommandByKey([string]$Key) {
  return $script:Commands | Where-Object { [string]$_.Key -eq $Key } | Select-Object -First 1
}
function Get-FrontDoorState {
  $fallback=[pscustomobject]@{
    localPatch=(Get-CurrentAcceptedPass); repositoryPatch=$null; repositoryCommit=$null
    gateId=$null; gateState='NONE'; syncState='NO_CERTIFICATION'; gitState=(Get-GitState)
    publicationEligible=$false; governedPathCount=$null
  }
  try {
    $authority=Join-Path $PSScriptRoot 'HavenwildGateAuthority.py'
    $python=Get-Command python -ErrorAction SilentlyContinue
    if($null -eq $python){ $python=Get-Command py -ErrorAction SilentlyContinue }
    if($null -eq $python -or -not (Test-Path -LiteralPath $authority -PathType Leaf)){ return $fallback }
    $raw=@(& $python.Source $authority frontdoor --root $Root 2>$null)
    if($LASTEXITCODE -ne 0 -or $raw.Count -eq 0){ return $fallback }
    return (($raw -join "`n") | ConvertFrom-Json)
  } catch { return $fallback }
}
function Get-PendingRootPatchCount {
  $seen=@{}
  foreach($pattern in @('Havenwild_IncrementalPatch_*.zip','Havenwild_Patch_*.zip','Havenwild_Handoff_*.zip')) {
    foreach($candidate in @(Get-ChildItem -LiteralPath $Root -File -Filter $pattern -ErrorAction SilentlyContinue)) { $seen[$candidate.FullName.ToLowerInvariant()]=$true }
  }
  return $seen.Count
}
function Get-CertifiedCommitMessage {
  try {
    if(Test-Path -LiteralPath $script:GreenGateMarker -PathType Leaf) {
      $marker=Get-Content -LiteralPath $script:GreenGateMarker -Raw | ConvertFrom-Json
      $patch=[string]$marker.pass
      if(-not [string]::IsNullOrWhiteSpace($patch)) { return ("Havenwild {0} - certified GREEN" -f $patch) }
    }
  } catch {}
  return (Get-DefaultCommitMessage)
}
function Invoke-RootGreenPublication {
  $state=Get-FrontDoorState
  if([string]$state.gateState -ne 'GREEN' -or -not [bool]$state.publicationEligible) {
    Write-Color 'PUBLICATION BLOCKED: current governed source is not certified GREEN.' Red
    Write-Color 'Run option 1 - FULL QUALITY GATE / CERTIFY GREEN first.' Yellow
    $script:LastName='Publish current GREEN'; $script:LastResult='FAIL'; $script:LastActionExitCode=1
    return
  }
  $message=Get-CertifiedCommitMessage
  Write-Color ("Publishing certified patch: {0}" -f [string]$state.localPatch) Cyan
  Write-Color ("Repository baseline       : {0}" -f [string]$state.repositoryPatch) DarkGray
  Write-Color ("Commit message            : {0}" -f $message) DarkGray
  Invoke-GitSourceAction 'CommitPushGreen' $message
}
function Show-Header {
  Clear-Host
  $state=Get-FrontDoorState
  $git=[string]$state.gitState; $editor=Get-BuildState "haven_editor_native.exe"; $client=Get-BuildState "haven_game.exe"; $baseline=Get-BaselineState
  $localPatch=if([string]::IsNullOrWhiteSpace([string]$state.localPatch)){'<unknown>'}else{[string]$state.localPatch}
  $repoPatch=if([string]::IsNullOrWhiteSpace([string]$state.repositoryPatch)){if([string]::IsNullOrWhiteSpace([string]$state.repositoryCommit)){'<none>'}else{"commit " + ([string]$state.repositoryCommit).Substring(0,[Math]::Min(8,([string]$state.repositoryCommit).Length))}}else{[string]$state.repositoryPatch}
  $sync=[string]$state.syncState
  $gate=if([string]$state.gateState -eq 'GREEN'){"GREEN " + $localPatch}elseif([string]$state.gateState -eq 'STALE'){"STALE - recertify"}else{[string]$state.gateState}
  Write-Color "========================================================================" DarkCyan
  Write-Color " HAVENWILD PROJECT CONTROL CENTER" Cyan
  Write-Color "========================================================================" DarkCyan
  Write-Color (" Repository : {0}" -f $Root) Gray
  Write-Color (" Git        : {0}" -f $git) $(if($git -eq 'Clean'){'Green'}elseif($git -like 'Modified*'){'Yellow'}else{'DarkGray'})
  Write-Color (" Editor     : {0}" -f $editor) $(if($editor -eq 'Ready'){'Green'}else{'Yellow'})
  Write-Color (" Client     : {0}" -f $client) $(if($client -eq 'Ready'){'Green'}else{'Yellow'})
  Write-Color (" Baseline   : {0}" -f $baseline) $(if($baseline -eq 'Ready'){'Green'}else{'Yellow'})
  Write-Color (" Local      : {0}" -f $localPatch) $(if([string]$state.gateState -eq 'GREEN'){'Green'}else{'Yellow'})
  Write-Color (" Repository : {0}" -f $repoPatch) Gray
  Write-Color (" Sync       : {0}" -f $sync) $(if($sync -eq 'MATCH'){'Green'}elseif($sync -like '*GREEN*'){'Yellow'}elseif($sync -like '*STALE*'){'Red'}else{'Yellow'})
  Write-Color (" Gate       : {0}" -f $gate) $(if([string]$state.gateState -eq 'GREEN'){'Green'}elseif([string]$state.gateState -eq 'STALE'){'Red'}else{'DarkGray'})
  Write-Color (" Updates    : {0} pending" -f (Get-PendingRootPatchCount)) DarkGray
  Write-Color (" Last       : {0} [{1}] in {2}" -f $script:LastName,$script:LastResult,$script:LastDuration) $(if($script:LastResult -eq 'PASS'){'Green'}elseif($script:LastResult -eq 'FAIL'){'Red'}else{'Gray'})
  Write-Color (" Active log : {0}" -f $SessionLog) DarkGray
  foreach ($startupWarning in $script:StartupWarnings) { Write-Color (" Startup    : WARNING - {0}" -f $startupWarning) Yellow }
  Write-Color "------------------------------------------------------------------------" DarkCyan
}
function Invoke-HavenwildAction([string]$Name,[scriptblock]$Action,[string]$Category="sessions") {
  $start=Get-Date; $script:LastName=$Name
  $categoryPath=Join-Path $LogRoot $Category; New-Item -ItemType Directory -Force -Path $categoryPath | Out-Null
  $actionLog=Join-Path $categoryPath ("{0}-{1}.log" -f (($Name -replace '[^A-Za-z0-9]+','-').Trim('-').ToLower()),(Get-Date -Format 'yyyyMMdd-HHmmss'))
  Write-Color ""; Write-Color ("START {0}" -f $Name) Cyan; Write-Color ("Action log: {0}" -f $actionLog) DarkGray
  $result='PASS'; $exitCode=0; $failureMessage=$null
  try {
    $global:LASTEXITCODE=0
    & $Action 2>&1 | Tee-Object -FilePath $actionLog -Append | ForEach-Object { Write-Host $_; Add-Content $SessionLog $_ }
    $code=$LASTEXITCODE; if($null -eq $code){$code=0}
    if($code -ne 0){ throw "Command exited with code $code" }
    $script:LastResult='PASS'; $script:LastActionExitCode=0
    Write-Color ("PASS {0}" -f $Name) Green
  } catch {
    $result='FAIL'; $exitCode=1; $failureMessage=$_.Exception.Message
    $script:LastResult='FAIL'; $script:LastActionExitCode=1
    Write-Color ("FAIL {0}: {1}" -f $Name,$failureMessage) Red
  }
  $elapsed=((Get-Date)-$start).TotalSeconds
  $script:LastDuration=('{0:N1}s' -f $elapsed)
  Write-Color ("Duration: {0}" -f $script:LastDuration) DarkGray
  if($script:QualityGateActive) {
    $script:QualityGateActionLogs += $actionLog
    $script:QualityGateActions += [ordered]@{
      key=if([string]::IsNullOrWhiteSpace([string]$script:CurrentCommandKey)){$Name}else{[string]$script:CurrentCommandKey}
      name=$Name
      category=$Category
      result=$result
      exitCode=$exitCode
      durationSeconds=[Math]::Round($elapsed,3)
      log=$actionLog
      failure=$failureMessage
    }
  }
  Refresh-ArtifactIndex -Quiet
}
function Test-ControlCenterRestartChild {
  if($Command -eq 'menu') { return $false }
  try {
    $currentProcess=Get-CimInstance Win32_Process -Filter ("ProcessId={0}" -f $PID) -ErrorAction Stop
    if($null -eq $currentProcess -or $null -eq $currentProcess.ParentProcessId) { return $false }
    $parentProcess=Get-CimInstance Win32_Process -Filter ("ProcessId={0}" -f $currentProcess.ParentProcessId) -ErrorAction Stop
    if($null -eq $parentProcess) { return $false }
    return ([string]$parentProcess.CommandLine -match 'HavenwildTools\.ps1')
  } catch {
    return $false
  }
}
function Open-Path([string]$Path){ if(Test-Path $Path){ Start-Process explorer.exe $Path } else { Write-Color "Missing path: $Path" Yellow } }
function Initialize-StandardArtifactFolders {
  foreach($relative in @('artifacts\packages','artifacts\recovery','artifacts\debug-bundles','artifacts\troubleshooting-bundles','artifacts\updates\applied','artifacts\updates\failed','artifacts\updates\undone','.havenwild\quality-gates','.havenwild\fast-gates','.havenwild\updates\history','.havenwild\updates\restore-staging')) {
    $path = Join-Path $Root $relative
    if(-not (Test-Path -LiteralPath $path -PathType Container)) {
      New-Item -ItemType Directory -Force -Path $path | Out-Null
    }
  }
}
function Write-JsonAtomic {
  param([Parameter(Mandatory=$true)][string]$Path,[Parameter(Mandatory=$true)][object]$Value)
  $parent=Split-Path -Parent $Path
  if(-not [string]::IsNullOrWhiteSpace($parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
  $tmp="$Path.tmp-$([guid]::NewGuid().ToString('N'))"
  try {
    ($Value | ConvertTo-Json -Depth 12) + [Environment]::NewLine | Set-Content -LiteralPath $tmp -Encoding UTF8
    Move-Item -LiteralPath $tmp -Destination $Path -Force
  } finally {
    Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
  }
}
function Get-GreenGateSummary {
  if(-not (Test-Path -LiteralPath $script:GreenGateMarker -PathType Leaf)) { return 'None' }
  try {
    $marker=Get-Content -LiteralPath $script:GreenGateMarker -Raw | ConvertFrom-Json
    $passLabel=if([string]::IsNullOrWhiteSpace([string]$marker.pass) -or [string]$marker.pass -eq 'manual'){'checkpoint'}else{[string]$marker.pass}
    return ("GREEN {0}" -f $passLabel)
  } catch { return 'Marker unreadable' }
}
function Get-CurrentAcceptedPass {
  $lastApplied=Join-Path $Root '.havenwild\updates\last-applied.json'
  if(Test-Path -LiteralPath $lastApplied -PathType Leaf) {
    try {
      $state=Get-Content -LiteralPath $lastApplied -Raw | ConvertFrom-Json
      if(-not [string]::IsNullOrWhiteSpace([string]$state.pass)) { return [string]$state.pass }
    } catch {}
  }
  if(-not [string]::IsNullOrWhiteSpace($Pass) -and $Pass -ne 'manual') { return $Pass }
  return 'manual'
}
function Get-SourceRollupPointer {
  $pointer=Join-Path $Root 'artifacts\packages\LATEST_SOURCE_ROLLUP.txt'
  if(-not (Test-Path -LiteralPath $pointer -PathType Leaf)) { return $null }
  $result=[ordered]@{ pointer=$pointer; path=$null; sha256=$null }
  foreach($line in Get-Content -LiteralPath $pointer -ErrorAction SilentlyContinue) {
    if($line -match '^Path:\s*(.+)$') { $result.path=$Matches[1].Trim() }
    elseif($line -match '^SHA-256:\s*([0-9a-fA-F]{64})$') { $result.sha256=$Matches[1].ToLowerInvariant() }
  }
  return $result
}
function Get-RecoveryRollupPointer {
  $pointer=Join-Path $Root 'artifacts\recovery\LATEST_RECOVERY_ROLLUP.txt'
  if(-not (Test-Path -LiteralPath $pointer -PathType Leaf)) { return $null }
  $result=[ordered]@{ pointer=$pointer; path=$null; sha256=$null; backup=$null }
  foreach($line in Get-Content -LiteralPath $pointer -ErrorAction SilentlyContinue) {
    if($line -match '^ZIP=(.+)$') { $result.path=$Matches[1].Trim() }
    elseif($line -match '^SHA256=([0-9a-fA-F]{64})$') { $result.sha256=$Matches[1].ToLowerInvariant() }
    elseif($line -match '^BACKUP=(.+)$') { $result.backup=$Matches[1].Trim() }
  }
  return $result
}
function Get-LatestFileRecursive([string]$Directory,[string]$Filter='*') {
  if(-not (Test-Path -LiteralPath $Directory -PathType Container)) { return $null }
  return Get-ChildItem -LiteralPath $Directory -File -Recurse -Filter $Filter -ErrorAction SilentlyContinue | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
}
function Get-LatestQualityGateRecord {
  if(Test-Path -LiteralPath $script:LatestQualityGatePath -PathType Leaf) {
    try { return Get-Content -LiteralPath $script:LatestQualityGatePath -Raw | ConvertFrom-Json } catch {}
  }
  return $null
}
function Write-QualityGateRunRecord([string]$Result) {
  if([string]::IsNullOrWhiteSpace([string]$script:QualityGateRunId)) { return }
  try {
    New-Item -ItemType Directory -Force -Path $script:QualityGateHistoryRoot | Out-Null
    $ended=Get-Date
    $duration=if($null -eq $script:QualityGateStarted){0}else{($ended-$script:QualityGateStarted).TotalSeconds}
    $payload=[ordered]@{
      schema='havenwild.quality_gate_run.v1'
      runId=$script:QualityGateRunId
      result=$Result
      pass=Get-CurrentAcceptedPass
      startedUtc=if($null -eq $script:QualityGateStarted){$null}else{$script:QualityGateStarted.ToUniversalTime().ToString('o')}
      endedUtc=$ended.ToUniversalTime().ToString('o')
      durationSeconds=[Math]::Round($duration,3)
      repository=$Root
      sessionLog=$SessionLog
      debugBundle=$script:LastDebugBundlePath
      actions=@($script:QualityGateActions)
    }
    $runPath=Join-Path $script:QualityGateHistoryRoot ("{0}.json" -f $script:QualityGateRunId)
    Write-JsonAtomic -Path $runPath -Value $payload
    Write-JsonAtomic -Path $script:LatestQualityGatePath -Value $payload
    Write-Color ("QUALITY GATE RECORD: {0}" -f $runPath) DarkGray
  } catch {
    Write-Color ("Quality gate history warning: {0}" -f $_.Exception.Message) Yellow
  }
}
function Invoke-QualityGateHistory {
  Invoke-HavenwildAction 'Quality gate history' {
    $records=@()
    if(Test-Path -LiteralPath $script:QualityGateHistoryRoot -PathType Container) {
      foreach($file in Get-ChildItem -LiteralPath $script:QualityGateHistoryRoot -File -Filter 'QG-*.json' -ErrorAction SilentlyContinue | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 12) {
        try { $records += Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json } catch {}
      }
    }
    if($records.Count -eq 0) { Write-Output 'No persistent Full Quality Gate records exist yet.'; return }
    Write-Output 'Recent Full Quality Gates:'
    foreach($record in $records) {
      $started=try{([datetime]$record.startedUtc).ToLocalTime().ToString('yyyy-MM-dd HH:mm:ss')}catch{[string]$record.startedUtc}
      Write-Output ("- {0}  {1}  pass={2}  duration={3:N1}s  started={4}" -f $record.runId,$record.result,$record.pass,[double]$record.durationSeconds,$started)
      foreach($action in @($record.actions)) {
        Write-Output ("    {0,-5} {1} ({2:N1}s)" -f $action.result,$action.name,[double]$action.durationSeconds)
      }
      if(-not [string]::IsNullOrWhiteSpace([string]$record.debugBundle)) { Write-Output ("    debug: {0}" -f $record.debugBundle) }
    }
  } 'diagnostics'
}
function Write-FastGateRunRecord([string]$Result) {
  if([string]::IsNullOrWhiteSpace([string]$script:QualityGateRunId)) { return }
  try {
    New-Item -ItemType Directory -Force -Path $script:FastGateHistoryRoot | Out-Null
    $ended=Get-Date
    $duration=if($null -eq $script:QualityGateStarted){0}else{($ended-$script:QualityGateStarted).TotalSeconds}
    $payload=[ordered]@{
      schema='havenwild.fast_gate_run.v1'
      runId=$script:QualityGateRunId
      result=$Result
      pass=Get-CurrentAcceptedPass
      startedUtc=if($null -eq $script:QualityGateStarted){$null}else{$script:QualityGateStarted.ToUniversalTime().ToString('o')}
      endedUtc=$ended.ToUniversalTime().ToString('o')
      durationSeconds=[Math]::Round($duration,3)
      repository=$Root
      sessionLog=$SessionLog
      actions=@($script:QualityGateActions)
      certificationAuthority=$false
    }
    $runPath=Join-Path $script:FastGateHistoryRoot ("{0}.json" -f $script:QualityGateRunId)
    Write-JsonAtomic -Path $runPath -Value $payload
    Write-JsonAtomic -Path $script:LatestFastGatePath -Value $payload
    Write-Color ("FAST GATE RECORD: {0}" -f $runPath) DarkGray
  } catch {
    Write-Color ("Fast gate history warning: {0}" -f $_.Exception.Message) Yellow
  }
}
function Invoke-QualityGateComparison {
  Invoke-HavenwildAction 'Compare latest Full Quality Gates' {
    $files=@()
    if(Test-Path -LiteralPath $script:QualityGateHistoryRoot -PathType Container) {
      $files=@(Get-ChildItem -LiteralPath $script:QualityGateHistoryRoot -File -Filter 'QG-*.json' -ErrorAction SilentlyContinue | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 2)
    }
    if($files.Count -lt 2) { Write-Output 'Need at least two persistent Full Quality Gate records before a comparison is available.'; return }
    $newer=Get-Content -LiteralPath $files[0].FullName -Raw | ConvertFrom-Json
    $older=Get-Content -LiteralPath $files[1].FullName -Raw | ConvertFrom-Json
    $delta=[double]$newer.durationSeconds-[double]$older.durationSeconds
    Write-Output ("Newer: {0}  {1}  {2:N1}s" -f $newer.runId,$newer.result,[double]$newer.durationSeconds)
    Write-Output ("Older: {0}  {1}  {2:N1}s" -f $older.runId,$older.result,[double]$older.durationSeconds)
    Write-Output ("Total duration delta: {0:+0.0;-0.0;0.0}s" -f $delta)
    $oldByKey=@{}
    foreach($action in @($older.actions)) { $oldByKey[[string]$action.key]=$action }
    Write-Output 'Stage comparison:'
    foreach($action in @($newer.actions)) {
      $key=[string]$action.key
      if($oldByKey.ContainsKey($key)) {
        $old=$oldByKey[$key]
        $stageDelta=[double]$action.durationSeconds-[double]$old.durationSeconds
        Write-Output ("  {0,-28} {1,7:N1}s  delta={2:+0.0;-0.0;0.0}s  {3}->{4}" -f $key,[double]$action.durationSeconds,$stageDelta,[string]$old.result,[string]$action.result)
      } else {
        Write-Output ("  {0,-28} {1,7:N1}s  new-stage  {2}" -f $key,[double]$action.durationSeconds,[string]$action.result)
      }
    }
  } 'diagnostics'
}
function Invoke-CompilerWarningSummary {
  Invoke-HavenwildAction 'Compiler warning summary' {
    $buildRoot=Join-Path $LogRoot 'builds'
    if(-not (Test-Path -LiteralPath $buildRoot -PathType Container)) { Write-Output 'No build log directory exists yet.'; return }
    $candidates=@()
    foreach($pattern in @('build-all-*.log','run-tests-*.log')) {
      $latest=Get-ChildItem -LiteralPath $buildRoot -File -Filter $pattern -ErrorAction SilentlyContinue | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
      if($null -ne $latest) { $candidates += $latest }
    }
    if($candidates.Count -eq 0) { Write-Output 'No recent Build all / Run tests action logs were found.'; return }
    foreach($file in $candidates | Sort-Object FullName -Unique) {
      $lines=@(Get-Content -LiteralPath $file.FullName -ErrorAction SilentlyContinue)
      $warnings=@()
      $current=$null
      foreach($line in $lines) {
        if($line -match '^warning:\s+(.+)$') {
          if($null -ne $current) { $warnings += [pscustomobject]$current }
          $current=[ordered]@{ message=$Matches[1].Trim(); file='(unknown)' }
          continue
        }
        if($null -ne $current -and $line -match '^\s*-->\s+(.+?):\d+:\d+\s*$') { $current.file=$Matches[1].Trim() }
      }
      if($null -ne $current) { $warnings += [pscustomobject]$current }
      $unique=@($warnings | Sort-Object message,file -Unique)
      Write-Output ("{0}: warning occurrences={1}; unique warning/file pairs={2}" -f $file.Name,$warnings.Count,$unique.Count)
      if($unique.Count -gt 0) {
        Write-Output '  Top files:'
        foreach($group in $unique | Group-Object file | Sort-Object Count -Descending | Select-Object -First 10) {
          Write-Output ("    {0,3}  {1}" -f $group.Count,$group.Name)
        }
        Write-Output '  Unique warnings:'
        foreach($warning in $unique | Select-Object -First 20) {
          Write-Output ("    - {0} [{1}]" -f $warning.message,$warning.file)
        }
        if($unique.Count -gt 20) { Write-Output ("    ... {0} additional unique warnings" -f ($unique.Count-20)) }
      }
    }
  } 'diagnostics'
}
function Invoke-UpdateStatus {
  Invoke-HavenwildAction 'Patch / update status' {
    $pendingMap=@{}
    foreach($pattern in @('Havenwild_IncrementalPatch_*.zip','Havenwild_Patch_*.zip','Havenwild_Handoff_*.zip')) {
      foreach($candidate in @(Get-ChildItem -LiteralPath $Root -File -Filter $pattern -ErrorAction SilentlyContinue)) {
        $pendingMap[$candidate.FullName.ToLowerInvariant()]=$candidate
      }
    }
    $pending=@($pendingMap.Values)
    $updateRoot=Join-Path $Root '.havenwild\updates'
    $failedRoot=Join-Path $Root 'artifacts\updates\failed'
    $appliedRoot=Join-Path $Root 'artifacts\updates\applied'
    $undoneRoot=Join-Path $Root 'artifacts\updates\undone'
    $historyRoot=Join-Path $updateRoot 'history'
    $backupRoot=Join-Path $updateRoot 'backups'
    $stagingRoot=Join-Path $updateRoot 'staging'
    $failed=@(Get-ChildItem -LiteralPath $failedRoot -File -Recurse -Filter '*.zip' -ErrorAction SilentlyContinue)
    $applied=@(Get-ChildItem -LiteralPath $appliedRoot -File -Recurse -Filter '*.zip' -ErrorAction SilentlyContinue)
    $undone=@(Get-ChildItem -LiteralPath $undoneRoot -File -Recurse -Filter '*.zip' -ErrorAction SilentlyContinue)
    $history=@(Get-ChildItem -LiteralPath $historyRoot -File -Filter '*.json' -ErrorAction SilentlyContinue)
    $backups=@(Get-ChildItem -LiteralPath $backupRoot -Directory -ErrorAction SilentlyContinue)
    $staging=@(Get-ChildItem -LiteralPath $stagingRoot -Directory -ErrorAction SilentlyContinue)
    Write-Output ("Pending root patches : {0}" -f $pending.Count)
    foreach($patch in $pending | Sort-Object LastWriteTimeUtc) { Write-Output ("  - {0}" -f $patch.Name) }
    Write-Output ("Applied archives     : {0}" -f $applied.Count)
    Write-Output ("Failed archives      : {0}" -f $failed.Count)
    Write-Output ("Undone archives      : {0}" -f $undone.Count)
    Write-Output ("Patch history records: {0}" -f $history.Count)
    Write-Output ("Patch backups        : {0}" -f $backups.Count)
    Write-Output ("Staging directories  : {0}" -f $staging.Count)
    $lastApplied=Join-Path $updateRoot 'last-applied.json'
    if(Test-Path -LiteralPath $lastApplied -PathType Leaf) {
      try {
        $state=Get-Content -LiteralPath $lastApplied -Raw | ConvertFrom-Json
        Write-Output ("Last applied         : {0} ({1})" -f $state.pass,$state.patchId)
        $archiveValue=$null
        if($null -ne $state.PSObject.Properties['archivedZip']) { $archiveValue=[string]$state.archivedZip }
        elseif($null -ne $state.PSObject.Properties['archive']) { $archiveValue=[string]$state.archive }
        Write-Output ("Archive              : {0}" -f $archiveValue)
        if($null -ne $state.PSObject.Properties['backupSnapshot']) { Write-Output ("Backup snapshot      : {0}" -f $state.backupSnapshot) }
      } catch { Write-Output 'Last applied         : unreadable state file' }
    } else { Write-Output 'Last applied         : none' }
    $latestFailed=Get-LatestFileRecursive -Directory $failedRoot -Filter '*.zip'
    if($null -ne $latestFailed) { Write-Output ("Latest failed        : {0}" -f $latestFailed.FullName) }
    $lastUndo=Join-Path $updateRoot 'last-undo.json'
    if(Test-Path -LiteralPath $lastUndo -PathType Leaf) {
      try { $undo=Get-Content -LiteralPath $lastUndo -Raw | ConvertFrom-Json; Write-Output ("Last undo            : {0} ({1})" -f $undo.pass,$undo.patchId); Write-Output ("Undo recovery       : {0}" -f $undo.recoveryRollup) } catch { Write-Output 'Last undo            : unreadable state file' }
    }
  } 'updates'
}
function Invoke-EnvironmentDoctor {
  Invoke-HavenwildAction 'Environment doctor' {
    $critical=0; $warnings=0
    function Report([string]$Level,[string]$Message) {
      Write-Output ("{0}: {1}" -f $Level,$Message)
      if($Level -eq 'FAIL') { $script:DoctorCritical++ }
      elseif($Level -eq 'WARN') { $script:DoctorWarnings++ }
    }
    $script:DoctorCritical=0; $script:DoctorWarnings=0
    foreach($spec in @(
      @{Name='cargo'; Args=@('--version'); Required=$true},
      @{Name='rustc'; Args=@('--version'); Required=$true},
      @{Name='python'; Args=@('--version'); Required=$true},
      @{Name='bash'; Args=@('--version'); Required=$true},
      @{Name='git'; Args=@('--version'); Required=$false}
    )) {
      $cmd=Get-Command $spec.Name -ErrorAction SilentlyContinue
      if($null -eq $cmd) { Report $(if($spec.Required){'FAIL'}else{'WARN'}) ("{0} is not available on PATH" -f $spec.Name); continue }
      try { $version=((@(& $spec.Name @($spec.Args) 2>&1) -join ' ').Trim() -replace '\s+',' '); Report 'PASS' ("{0}: {1}" -f $spec.Name,$version) }
      catch { Report 'WARN' ("{0} exists at {1} but version query failed" -f $spec.Name,$cmd.Source) }
    }
    Write-Output ("PASS: PowerShell {0}" -f $PSVersionTable.PSVersion)
    foreach($relative in @('Cargo.toml','Cargo.lock','tools\build\Build.cmd','tools\build\Build.sh','tools\control\InvokeRootPatchIntake.ps1','tools\automation\validation\validation_runner.py','content\build\validator_registry_v3.json')) {
      $path=Join-Path $Root $relative
      if(Test-Path -LiteralPath $path -PathType Leaf) { Report 'PASS' ("contract present: {0}" -f $relative) } else { Report 'FAIL' ("required contract missing: {0}" -f $relative) }
    }
    $registry=Join-Path $Root 'content\build\validator_registry_v3.json'
    if(Test-Path -LiteralPath $registry -PathType Leaf) {
      try { $r=Get-Content -LiteralPath $registry -Raw | ConvertFrom-Json; Report 'PASS' ("validator registry {0} with {1} validators" -f $r.version,@($r.validators).Count) }
      catch { Report 'FAIL' ("validator registry JSON is unreadable: {0}" -f $_.Exception.Message) }
    }
    $stateRoot=Join-Path $Root '.havenwild'
    try {
      New-Item -ItemType Directory -Force -Path $stateRoot | Out-Null
      $probe=Join-Path $stateRoot (".doctor-{0}.tmp" -f [guid]::NewGuid().ToString('N'))
      'ok' | Set-Content -LiteralPath $probe -Encoding ASCII
      Remove-Item -LiteralPath $probe -Force
      Report 'PASS' '.havenwild state directory is writable'
    } catch { Report 'FAIL' (".havenwild state directory is not writable: {0}" -f $_.Exception.Message) }
    try {
      $drive=[System.IO.DriveInfo]::new([System.IO.Path]::GetPathRoot($Root))
      $freeGb=$drive.AvailableFreeSpace/1GB; $totalGb=$drive.TotalSize/1GB
      if($freeGb -lt 5) { Report 'WARN' ("disk free is low: {0:N1} GB of {1:N1} GB" -f $freeGb,$totalGb) } else { Report 'PASS' ("disk free: {0:N1} GB of {1:N1} GB" -f $freeGb,$totalGb) }
    } catch { Report 'WARN' ("disk-space query failed: {0}" -f $_.Exception.Message) }
    if(Get-Command cargo -ErrorAction SilentlyContinue) {
      Push-Location $Root
      try {
        $metadata=(@(& cargo metadata --no-deps --format-version 1 2>&1) -join "`n")
        if($LASTEXITCODE -eq 0) { try { $m=$metadata | ConvertFrom-Json; Report 'PASS' ("cargo metadata: {0} workspace packages" -f @($m.packages).Count) } catch { Report 'WARN' 'cargo metadata returned non-JSON output' } }
        else { Report 'FAIL' 'cargo metadata --no-deps failed' }
      } finally { Pop-Location }
    }
    Write-Output ("Gate                 : {0}" -f (Get-GreenGateSummary))
    Write-Output ("Current pass         : {0}" -f (Get-CurrentAcceptedPass))
    Write-Output ("Artifact index       : {0}" -f $script:ArtifactIndexPath)
    Write-Output ("Doctor summary       : {0} critical, {1} warning(s)" -f $script:DoctorCritical,$script:DoctorWarnings)
    if($script:DoctorCritical -gt 0) { throw ("Environment doctor found {0} critical issue(s)." -f $script:DoctorCritical) }
  } 'diagnostics'
}
function Invoke-InspectLatestRecovery {
  Invoke-HavenwildAction 'Inspect latest recovery rollup' {
    $pointer=Get-RecoveryRollupPointer
    if($null -eq $pointer -or [string]::IsNullOrWhiteSpace([string]$pointer.path)) { throw 'No latest recovery rollup pointer is available.' }
    $zip=[string]$pointer.path
    if(-not (Test-Path -LiteralPath $zip -PathType Leaf)) { throw ("Recovery ZIP is missing: {0}" -f $zip) }
    $actual=(Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash.ToLowerInvariant()
    if(-not [string]::IsNullOrWhiteSpace([string]$pointer.sha256) -and $actual -ne [string]$pointer.sha256) { throw 'Recovery ZIP SHA-256 does not match LATEST_RECOVERY_ROLLUP.txt.' }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive=[IO.Compression.ZipFile]::OpenRead($zip)
    try {
      $entry=$archive.Entries | Where-Object { $_.FullName -eq 'RECOVERY_MANIFEST.json' } | Select-Object -First 1
      if($null -eq $entry) { throw 'RECOVERY_MANIFEST.json is missing from the recovery ZIP.' }
      $reader=New-Object IO.StreamReader($entry.Open(),[Text.Encoding]::UTF8,$true)
      try { $manifest=$reader.ReadToEnd() | ConvertFrom-Json } finally { $reader.Dispose() }
      if([string]$manifest.schema -ne 'havenwild.recovery_rollup.v1') { throw ("Unsupported recovery schema: {0}" -f $manifest.schema) }
      Write-Output ("Recovery ZIP         : {0}" -f $zip)
      Write-Output ("SHA-256             : {0}" -f $actual)
      Write-Output ("Created UTC          : {0}" -f $manifest.createdAtUtc)
      Write-Output ("Backup snapshot      : {0}" -f $manifest.backupSnapshot)
      Write-Output ("Backup files         : {0}" -f $manifest.backupFileCount)
      Write-Output ("Manifest entries     : {0}" -f @($manifest.entries).Count)
      Write-Output ("Current counterparts : {0}" -f $manifest.currentCounterpartsIncluded)
      Write-Output ("Recent logs          : {0}" -f $manifest.recentLogsIncluded)
      $roles=@($manifest.entries | Group-Object role | Sort-Object Name)
      foreach($role in $roles) { Write-Output ("  {0,-24} {1}" -f $role.Name,$role.Count) }
      Write-Output 'PASS: outer checksum and recovery manifest are valid.'
    } finally { $archive.Dispose() }
  } 'diagnostics'
}
function Refresh-ArtifactIndex {
  param([switch]$Quiet)
  try {
    $source=Get-SourceRollupPointer
    $recovery=Get-RecoveryRollupPointer
    $debugRoot=Join-Path $Root 'artifacts\debug-bundles'
    $debug=$null
    if(Test-Path -LiteralPath $debugRoot -PathType Container) {
      $debug=Get-ChildItem -LiteralPath $debugRoot -File -Filter 'Havenwild_DebugBundle_*.zip' -ErrorAction SilentlyContinue | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
    }
    $latestPackage=$null
    $packageRoot=Join-Path $Root 'artifacts\packages'
    if(Test-Path -LiteralPath $packageRoot -PathType Container) {
      $latestPackage=Get-ChildItem -LiteralPath $packageRoot -File -Filter '*.zip' -ErrorAction SilentlyContinue | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
    }
    $lastAppliedPath=Join-Path $Root '.havenwild\updates\last-applied.json'
    $lastApplied=$null
    if(Test-Path -LiteralPath $lastAppliedPath -PathType Leaf) {
      try { $lastApplied=Get-Content -LiteralPath $lastAppliedPath -Raw | ConvertFrom-Json } catch {}
    }
    $payload=[ordered]@{
      schema='havenwild.artifact_index.v1'
      updatedUtc=(Get-Date).ToUniversalTime().ToString('o')
      pass=Get-CurrentAcceptedPass
      activeSessionLog=$SessionLog
      greenGate=[ordered]@{ path=$script:GreenGateMarker; exists=(Test-Path -LiteralPath $script:GreenGateMarker -PathType Leaf) }
      lastAppliedUpdate=if($null -eq $lastApplied){$null}else{
        $appliedArchive=$null
        if($null -ne $lastApplied.PSObject.Properties['archivedZip']) { $appliedArchive=[string]$lastApplied.archivedZip }
        elseif($null -ne $lastApplied.PSObject.Properties['archive']) { $appliedArchive=[string]$lastApplied.archive }
        [ordered]@{ path=$lastAppliedPath; pass=[string]$lastApplied.pass; patchId=[string]$lastApplied.patchId; archive=$appliedArchive; backupSnapshot=if($null -ne $lastApplied.PSObject.Properties['backupSnapshot']){[string]$lastApplied.backupSnapshot}else{$null} }
      }
      lastUndo=if(-not (Test-Path -LiteralPath (Join-Path $Root '.havenwild\updates\last-undo.json') -PathType Leaf)){$null}else{
        $undoPath=Join-Path $Root '.havenwild\updates\last-undo.json'
        try { $undoState=Get-Content -LiteralPath $undoPath -Raw | ConvertFrom-Json; [ordered]@{ path=$undoPath; pass=[string]$undoState.pass; patchId=[string]$undoState.patchId; undoneUtc=[string]$undoState.undoneUtc; recoveryRollup=[string]$undoState.recoveryRollup; archivedZip=[string]$undoState.archivedZip } } catch { $null }
      }
      latestSourceRollup=$source
      latestRecoveryRollup=$recovery
      latestDebugBundle=if($null -eq $debug){$null}else{[ordered]@{ path=$debug.FullName; sha256=(Get-FileHash -LiteralPath $debug.FullName -Algorithm SHA256).Hash.ToLowerInvariant(); modifiedUtc=$debug.LastWriteTimeUtc.ToString('o') }}
      latestQualityGate=if($null -eq (Get-LatestQualityGateRecord)){$null}else{[ordered]@{ path=$script:LatestQualityGatePath; runId=[string](Get-LatestQualityGateRecord).runId; result=[string](Get-LatestQualityGateRecord).result; pass=[string](Get-LatestQualityGateRecord).pass; startedUtc=[string](Get-LatestQualityGateRecord).startedUtc }}
      latestFastGate=if(-not (Test-Path -LiteralPath $script:LatestFastGatePath -PathType Leaf)){$null}else{try{$fastState=Get-Content -LiteralPath $script:LatestFastGatePath -Raw | ConvertFrom-Json; [ordered]@{ path=$script:LatestFastGatePath; runId=[string]$fastState.runId; result=[string]$fastState.result; pass=[string]$fastState.pass; startedUtc=[string]$fastState.startedUtc }}catch{$null}}
      latestFailedUpdate=if($null -eq (Get-LatestFileRecursive -Directory (Join-Path $Root 'artifacts\updates\failed') -Filter '*.zip')){$null}else{
        $failed=Get-LatestFileRecursive -Directory (Join-Path $Root 'artifacts\updates\failed') -Filter '*.zip'
        [ordered]@{ path=$failed.FullName; modifiedUtc=$failed.LastWriteTimeUtc.ToString('o') }
      }
      latestUndoneUpdate=if($null -eq (Get-LatestFileRecursive -Directory (Join-Path $Root 'artifacts\updates\undone') -Filter '*.zip')){$null}else{
        $undone=Get-LatestFileRecursive -Directory (Join-Path $Root 'artifacts\updates\undone') -Filter '*.zip'
        [ordered]@{ path=$undone.FullName; modifiedUtc=$undone.LastWriteTimeUtc.ToString('o') }
      }
      latestPackage=if($null -eq $latestPackage){$null}else{
        $packageSha=$null
        $sidecar="$($latestPackage.FullName).sha256"
        if(Test-Path -LiteralPath $sidecar -PathType Leaf) {
          $firstLine=Get-Content -LiteralPath $sidecar -TotalCount 1 -ErrorAction SilentlyContinue
          if($firstLine -match '^([0-9a-fA-F]{64})') { $packageSha=$Matches[1].ToLowerInvariant() }
        }
        [ordered]@{ path=$latestPackage.FullName; sha256=$packageSha; modifiedUtc=$latestPackage.LastWriteTimeUtc.ToString('o') }
      }
    }
    Write-JsonAtomic -Path $script:ArtifactIndexPath -Value $payload
    if(-not $Quiet) { Write-Color ("ARTIFACT INDEX: {0}" -f $script:ArtifactIndexPath) DarkGray }
  } catch {
    if(-not $Quiet) { Write-Color ("Artifact index warning: {0}" -f $_.Exception.Message) Yellow }
  }
}
function Resolve-LatestArtifactPath([string]$Artifact) {
  Refresh-ArtifactIndex -Quiet
  if($Artifact -eq 'artifact-index') { return $script:ArtifactIndexPath }
  if(-not (Test-Path -LiteralPath $script:ArtifactIndexPath -PathType Leaf)) { return $null }
  try {
    $index=Get-Content -LiteralPath $script:ArtifactIndexPath -Raw | ConvertFrom-Json
    switch($Artifact) {
      'source-rollup' { return [string]$index.latestSourceRollup.path }
      'recovery' { return [string]$index.latestRecoveryRollup.path }
      'debug-bundle' { return [string]$index.latestDebugBundle.path }
      'quality-gate' { return [string]$index.latestQualityGate.path }
      'fast-gate' { return [string]$index.latestFastGate.path }
      'failed-update' { return [string]$index.latestFailedUpdate.path }
      'undone-update' { return [string]$index.latestUndoneUpdate.path }
      'undo-record' { return [string]$index.lastUndo.path }
    }
  } catch {}
  return $null
}
function Open-LatestArtifact([string]$Artifact) {
  $path=Resolve-LatestArtifactPath $Artifact
  if([string]::IsNullOrWhiteSpace($path) -or -not (Test-Path -LiteralPath $path)) {
    Write-Color ("No current artifact is available for: {0}" -f $Artifact) Yellow
    return
  }
  if($Artifact -in @('artifact-index','quality-gate','fast-gate','undo-record')) {
    Start-Process notepad.exe $path
    return
  }
  Start-Process explorer.exe -ArgumentList ('/select,"{0}"' -f $path)
}
function Get-ControlCenterRegistryIssues {
  $issues=@()
  $allowedMenus=@('build','run','world','assets','project','package','logs')
  $allowedKinds=@('Build','Script','Package','Dependencies','LatestLog','Open','OpenArtifact','ControlSelfTest','EnvironmentDoctor','QualityGateHistory','UpdateStatus','RecoveryInspect','QualityGateCompare','CompilerWarningSummary','DebugBundle','Help','BuiltinQualityGate','BuiltinFastQualityGate')
  $ids=@{}; $keys=@{}
  foreach($entry in $script:Commands) {
    $id=[string]$entry.Id; $key=[string]$entry.Key; $label=[string]$entry.Label; $kind=[string]$entry.Kind
    if([string]::IsNullOrWhiteSpace($id)) { $issues += 'A registered command has no Id.' }
    elseif($ids.ContainsKey($id)) { $issues += ("Duplicate command Id: {0}" -f $id) } else { $ids[$id]=$true }
    if([string]::IsNullOrWhiteSpace($key)) { $issues += ("Command {0} has no stable Key." -f $id) }
    elseif($keys.ContainsKey($key)) { $issues += ("Duplicate command Key: {0}" -f $key) } else { $keys[$key]=$true }
    if([string]::IsNullOrWhiteSpace($label)) { $issues += ("Command {0} has no Label." -f $id) }
    if([string]::IsNullOrWhiteSpace($kind)) { $issues += ("Command {0} has no Kind." -f $id) }
    elseif($allowedKinds -notcontains $kind) { $issues += ("Command {0} has unsupported Kind {1}." -f $id,$kind) }
    foreach($menu in @($entry.Menu)) { if($allowedMenus -notcontains [string]$menu) { $issues += ("Command {0} references unknown menu {1}." -f $id,$menu) } }
    if($kind -eq 'Script') {
      $scriptPath=Join-Path $PSScriptRoot ([string]$entry.Script)
      if(-not (Test-Path -LiteralPath $scriptPath -PathType Leaf)) { $issues += ("Command {0} script is missing: {1}" -f $id,$scriptPath) }
    }
  }
  foreach($requiredKey in @('validation.full-quality-gate','validation.fast-quality-gate','doctor.environment','validation.quality-gate-history','validation.compare-quality-gates','diagnostics.compiler-warnings','updates.status','recovery.inspect-latest','recovery.preview-undo-latest','recovery.undo-latest')) {
    if($null -eq (Get-CommandByKey $requiredKey)) { $issues += ("Required Control Center command is not registered by stable key: {0}" -f $requiredKey) }
  }
  foreach($required in @('tools\build\Build.cmd','tools\build\Build.sh','tools\control\RestoreLatestPatchBackup.ps1','content\build\validator_registry_v3.json')) {
    if(-not (Test-Path -LiteralPath (Join-Path $Root $required) -PathType Leaf)) { $issues += ("Required Control Center dependency is missing: {0}" -f $required) }
  }
  $validatorRegistry=Join-Path $Root 'content\build\validator_registry_v3.json'
  if(Test-Path -LiteralPath $validatorRegistry -PathType Leaf) {
    try { $vr=Get-Content -LiteralPath $validatorRegistry -Raw | ConvertFrom-Json; if([string]$vr.schema -ne 'havenwild.validator.registry.v3'){ $issues += ("Unexpected validator registry schema: {0}" -f $vr.schema) } } catch { $issues += ("Validator registry JSON is unreadable: {0}" -f $_.Exception.Message) }
  }
  return @($issues)
}
function Invoke-ControlCenterSelfTest {
  Invoke-HavenwildAction 'Control Center self-test' {
    $issues=@(Get-ControlCenterRegistryIssues)
    if($issues.Count -gt 0) {
      foreach($issue in $issues) { Write-Output ("FAIL: {0}" -f $issue) }
      throw ("Control Center self-test found {0} issue(s)." -f $issues.Count)
    }
    Write-Output ("PASS: {0} registered commands have unique stable IDs/keys and valid menu routes." -f $script:Commands.Count)
    Write-Output 'PASS: Build entrypoints and validator registry are present.'
    $controlSource=Get-Content -LiteralPath $PSCommandPath -Raw
    $legacyExitStateToken=('$script:' + 'LastExitCode')
    if($controlSource.Contains($legacyExitStateToken)) {
      throw 'Control Center action state must not shadow PowerShell automatic $LASTEXITCODE.'
    }
    Write-Output 'PASS: Control Center action exit state does not shadow PowerShell automatic $LASTEXITCODE.'
    if(-not $controlSource.Contains("`$gitDispatchArgs=@('-Root',`$Root,'-Action',`$Action,'-RemoteUrl',`$script:GitRemoteUrl)")) { throw 'GitHub menu dispatch must forward an explicit typed -Action argument.' }
    if($controlSource -match '(?im)^\s*\$args\s*=.*-Action') { throw 'GitHub dispatch must not reuse PowerShell automatic $args/$Args.' }
    Write-Output 'PASS: GitHub menu dispatch forwards explicit source-control actions without automatic $args collision.'
    if(-not $controlSource.Contains('[switch]$ReturnToMenu')) { throw 'Control Center self-update handoff must support returning to the interactive menu.' }
    if(-not $controlSource.Contains('Test-ControlCenterRestartChild')) { throw 'Control Center self-update bootstrap must detect a nested Control Center process.' }
    $restartOwnershipToken="if(`$script:ReturnToInteractiveMenu) { `$restartArgs += '-ReturnToMenu' }"
    if(-not $controlSource.Contains($restartOwnershipToken)) { throw 'Control Center self-update handoff must preserve interactive menu ownership.' }
    Write-Output 'PASS: Control Center self-update handoff preserves the interactive menu, including one-version bootstrap restarts.'
    $mainExitToken="if(`$choice -eq '0') { break }"
    if(-not $controlSource.Contains($mainExitToken)) { throw 'Main-menu Exit must break the outer interactive loop before switch dispatch.' }
    Write-Output 'PASS: Main-menu 0 exits the outer interactive Control Center loop.'
    Write-Output ("PASS: Artifact index authority is {0}" -f $script:ArtifactIndexPath)
  } 'diagnostics'
}
function Get-CommandsByMenu([string]$MenuKey) {
  return @($script:Commands | Where-Object { @($_.Menu) -contains $MenuKey } | Sort-Object @{Expression={ if($null -ne $_.MenuOrder){[int]$_.MenuOrder}else{9999} }}, @{Expression={ [int]$_.Id }})
}
function Get-MenuEntries([string]$MenuKey) {
  if($MenuKey -eq 'advanced') { return @($script:Commands | Sort-Object @{Expression={ [int]$_.Id }}) }
  return @(Get-CommandsByMenu $MenuKey)
}
function Show-StatusFooter {
  Write-Color "------------------------------------------------------------------------" DarkCyan
  Write-Color ("[Editor:{0}] [Client:{1}] [Baseline:{2}] [Git:{3}] [Last:{4} {5}]" -f (Get-BuildState 'haven_editor_native.exe'),(Get-BuildState 'haven_game.exe'),(Get-BaselineState),(Get-GitState),$script:LastResult,$script:LastDuration) DarkCyan
}
function Show-MainMenu {
  Write-Color "  1. FULL QUALITY GATE / CERTIFY GREEN" Green
  Write-Color "  2. COMMIT + PUSH CURRENT GREEN" Green
  Write-Color "" DarkGray
  Write-Color "  3. Build & verify" White
  Write-Color "  4. Run & play" White
  Write-Color "  5. World, terrain & scene tools" White
  Write-Color "  6. Asset authority & catalog" White
  Write-Color "  7. Project maintenance & diagnostics" White
  Write-Color "  8. Packaging & baselines" White
  Write-Color "  9. Logs & help" White
  Write-Color " 10. Advanced / all registered commands" DarkGray
  Write-Color " 11. Source control (GitHub optional)" White
  Write-Color "  0. Exit" DarkGray
  Show-StatusFooter
}
function Show-SubMenu([string]$Title,[object[]]$Entries) {
  Write-Color (" {0}" -f $Title.ToUpperInvariant()) Cyan
  Write-Color "------------------------------------------------------------------------" DarkCyan
  for($i=0; $i -lt $Entries.Count; $i++) {
    Write-Color (" {0,2}. {1}" -f ($i+1),([string]$Entries[$i].Label)) White
  }
  Write-Color "  0. Back" DarkGray
  Show-StatusFooter
}
function Invoke-GitHubMenu {
  do {
    Show-Header
    Write-Color " GITHUB / SOURCE CONTROL" Cyan
    Write-Color "------------------------------------------------------------------------" DarkCyan
    Write-Color "  1. Status / green-gate state" White
    Write-Color "  2. Initialize / connect this working folder to GitHub" White
    Write-Color "  3. Review GitHub-Core changes" White
    Write-Color "  4. Commit + push last GREEN Full Quality Gate" Green
    Write-Color "  5. Commit last GREEN Full Quality Gate (no push)" White
    Write-Color "  6. Push committed main to GitHub" White
    Write-Color "  7. Pull origin/main (fast-forward only)" White
    Write-Color "  8. Open Havenwild GitHub repository" White
    Write-Color "  9. Advanced manual commit (not green-gate protected)" DarkYellow
    Write-Color "  0. Back" DarkGray
    Show-StatusFooter
    $choice=Read-Host 'Select an option'
    switch($choice) {
      '0' { return }
      '1' { Invoke-GitSourceAction 'Status' }
      '2' { Invoke-GitSourceAction 'Setup' }
      '3' { Invoke-GitSourceAction 'Review' }
      '4' { $message=Read-CommitMessage; Invoke-GitSourceAction 'CommitPushGreen' $message }
      '5' { $message=Read-CommitMessage; Invoke-GitSourceAction 'CommitGreen' $message }
      '6' { Invoke-GitSourceAction 'Push' }
      '7' { Invoke-GitSourceAction 'Pull' }
      '8' { Invoke-GitSourceAction 'OpenRemote' }
      '9' {
        Write-Color 'WARNING: this commit is not protected by the last green Full Quality Gate.' Yellow
        $confirm=Read-Host 'Continue with an unverified manual commit? [y/N]'
        if($confirm -match '^[Yy]$') { $message=Read-CommitMessage; Invoke-GitSourceAction 'ManualCommit' $message }
      }
      default { Write-Color 'Unknown menu option.' Yellow; Start-Sleep -Milliseconds 650; continue }
    }
    Write-Color ''
    Read-Host 'Press Enter to return to GitHub / source control' | Out-Null
  } while($true)
}
function New-DebugBundle([string]$Result) {
  try {
    $bundleRoot=Join-Path $Root 'artifacts\debug-bundles'
    New-Item -ItemType Directory -Force -Path $bundleRoot | Out-Null
    $stamp=Get-Date -Format 'yyyyMMdd-HHmmss'
    $bundlePath=Join-Path $bundleRoot ("Havenwild_DebugBundle_{0}_{1}.zip" -f $stamp,$Result)
    $stage=Join-Path $bundleRoot (".stage-{0}-{1}" -f $stamp,[guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Force -Path $stage | Out-Null
    $logs=@()
    if($script:QualityGateActionLogs.Count -gt 0) {
      foreach($path in $script:QualityGateActionLogs) { if(Test-Path -LiteralPath $path -PathType Leaf) { $logs += Get-Item -LiteralPath $path } }
    } else {
      foreach($folder in @('diagnostics','builds','validation','sessions','updates')) {
        $path=Join-Path $LogRoot $folder
        if(Test-Path $path) { $logs += Get-ChildItem -LiteralPath $path -File -Filter '*.log' -ErrorAction SilentlyContinue | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 2 }
      }
    }
    if(Test-Path -LiteralPath $SessionLog -PathType Leaf) { $logs += Get-Item -LiteralPath $SessionLog }
    $logs=@($logs | Sort-Object FullName -Unique | Sort-Object LastWriteTimeUtc)
    $logEntries=@()
    foreach($log in $logs) {
      $destination=Join-Path $stage $log.Name
      Copy-Item -LiteralPath $log.FullName -Destination $destination -Force
      $logEntries += [ordered]@{ name=$log.Name; source=$log.FullName; sha256=(Get-FileHash -LiteralPath $log.FullName -Algorithm SHA256).Hash.ToLowerInvariant(); bytes=$log.Length }
    }
    foreach($stateFile in @($script:GreenGateMarker,(Join-Path $Root '.havenwild\updates\last-applied.json'))) {
      if(Test-Path -LiteralPath $stateFile -PathType Leaf) { Copy-Item -LiteralPath $stateFile -Destination (Join-Path $stage ([System.IO.Path]::GetFileName($stateFile))) -Force }
    }
    # Validation reports contain structured failure details that console logs can
    # intentionally abbreviate. Keep the newest JSON/Markdown pair in every
    # debug handoff so read-only mutation failures identify the exact paths.
    $validationLogRoot=Join-Path $LogRoot 'validation'
    if(Test-Path -LiteralPath $validationLogRoot -PathType Container) {
      foreach($pattern in @('validation-*.json','validation-*.md')) {
        $report=Get-ChildItem -LiteralPath $validationLogRoot -File -Filter $pattern -ErrorAction SilentlyContinue | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
        if($null -ne $report) { Copy-Item -LiteralPath $report.FullName -Destination (Join-Path $stage $report.Name) -Force }
      }
    }
    # A compact Git snapshot distinguishes intended patch deltas from unexpected
    # writers that touch protected project sources during a read-only validator.
    if(Get-Command git -ErrorAction SilentlyContinue) {
      Push-Location $Root
      try {
        $oldPreference=$ErrorActionPreference; $ErrorActionPreference='Continue'
        try { $gitStatus=@(& git status --short --branch 2>&1) } finally { $ErrorActionPreference=$oldPreference }
      } finally { Pop-Location }
      Set-Content -LiteralPath (Join-Path $stage 'git-status.txt') -Value $gitStatus -Encoding UTF8
    }
    $toolchain=[ordered]@{}
    foreach($spec in @(@('cargo','--version'),@('rustc','--version'),@('python','--version'),@('git','--version'))) {
      $exe=$spec[0]
      if(Get-Command $exe -ErrorAction SilentlyContinue) {
        try { $toolchain[$exe]=(@(& $exe $spec[1] 2>&1) -join ' ').Trim() } catch { $toolchain[$exe]='error' }
      } else { $toolchain[$exe]='unavailable' }
    }
    $contracts=[ordered]@{}
    foreach($relative in @('tools\control\ProjectCommandRegistry.ps1','tools\build\Build.sh','content\build\validator_registry_v3.json')) {
      $path=Join-Path $Root $relative
      if(Test-Path -LiteralPath $path -PathType Leaf) { $contracts[$relative]=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() }
    }
    $manifest=[ordered]@{
      schema='havenwild.debug_bundle.v2'
      createdUtc=(Get-Date).ToUniversalTime().ToString('o')
      result=$Result
      runId=$script:QualityGateRunId
      runStartedUtc=if($null -eq $script:QualityGateStarted){$null}else{$script:QualityGateStarted.ToUniversalTime().ToString('o')}
      pass=Get-CurrentAcceptedPass
      repository=$Root
      sessionLog=$SessionLog
      state=[ordered]@{ editor=Get-BuildState 'haven_editor_native.exe'; client=Get-BuildState 'haven_game.exe'; baseline=Get-BaselineState; git=Get-GitState; lastAction=$script:LastName; lastResult=$script:LastResult; lastDuration=$script:LastDuration }
      toolchain=$toolchain
      contracts=$contracts
      actions=@($script:QualityGateActions)
      artifactIndex=$script:ArtifactIndexPath
      logs=@($logEntries)
    }
    Write-JsonAtomic -Path (Join-Path $stage 'DEBUG_MANIFEST.json') -Value $manifest
    $status=@(
      'Havenwild debug bundle',
      ("Created: {0:o}" -f (Get-Date)),
      ("Result: {0}" -f $Result),
      ("RunId: {0}" -f $script:QualityGateRunId),
      ("Repository: {0}" -f $Root),
      ("Pass: {0}" -f (Get-CurrentAcceptedPass)),
      ("Editor: {0}" -f (Get-BuildState 'haven_editor_native.exe')),
      ("Client: {0}" -f (Get-BuildState 'haven_game.exe')),
      ("Baseline: {0}" -f (Get-BaselineState)),
      ("Git: {0}" -f (Get-GitState))
    )
    Set-Content -LiteralPath (Join-Path $stage 'STATUS.txt') -Value $status -Encoding UTF8
    Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $bundlePath -Force
    Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue
    $hash=(Get-FileHash -Algorithm SHA256 -LiteralPath $bundlePath).Hash.ToLowerInvariant()
    $script:LastDebugBundlePath=$bundlePath
    Write-Color ("DEBUG BUNDLE: {0}" -f $bundlePath) Cyan
    Write-Color ("DEBUG SHA-256: {0}" -f $hash) DarkGray
    Write-Color ("DEBUG LOG FILES: {0}" -f $logs.Count) DarkGray
    Refresh-ArtifactIndex -Quiet
  } catch {
    Write-Color ("Debug bundle warning: {0}" -f $_.Exception.Message) Yellow
  }
}

function Reveal-DebugHandoff([string]$BundlePath) {
  if([string]::IsNullOrWhiteSpace($BundlePath) -or -not (Test-Path -LiteralPath $BundlePath -PathType Leaf)) { return }
  try {
    $resolved=(Resolve-Path -LiteralPath $BundlePath).Path
    Start-Process explorer.exe -ArgumentList @('/select,',('"{0}"' -f $resolved))
    Write-Color ("DEBUG HANDOFF READY: {0}" -f $resolved) Cyan
  } catch { Write-Color ("Debug handoff reveal warning: {0}" -f $_.Exception.Message) Yellow }
}
function Publish-FailureDebugHandoff([string]$Result='FAIL') {
  try {
    $bundle=$script:LastDebugBundlePath
    if([string]::IsNullOrWhiteSpace($bundle) -or -not (Test-Path -LiteralPath $bundle -PathType Leaf)) { New-DebugBundle $Result; $bundle=$script:LastDebugBundlePath }
    Reveal-DebugHandoff $bundle
  } catch { Write-Color ("Failure debug handoff warning: {0}" -f $_.Exception.Message) Yellow }
}

function New-TroubleshootingBundle([string]$Result) {
  try {
    $bundleRoot=Join-Path $Root 'artifacts\troubleshooting-bundles'
    New-Item -ItemType Directory -Force -Path $bundleRoot | Out-Null
    $stamp=Get-Date -Format 'yyyyMMdd-HHmmss'
    $bundlePath=Join-Path $bundleRoot ("Havenwild_TroubleshootingBundle_{0}_{1}.zip" -f $stamp,$Result)
    $stage=Join-Path $bundleRoot (".stage-{0}-{1}" -f $stamp,[guid]::NewGuid().ToString('N').Substring(0,6))
    New-Item -ItemType Directory -Force -Path $stage | Out-Null
    $inventory=@()
    $maxFileBytes=25MB
    $sources=@(
      @{ Root=$LogRoot; Label='logs'; Pattern='*' },
      @{ Root=(Join-Path $Root '.havenwild\quality-gates'); Label='quality-gates'; Pattern='*.json' },
      @{ Root=(Join-Path $Root '.havenwild\fast-gates'); Label='fast-gates'; Pattern='*.json' },
      @{ Root=(Join-Path $Root '.havenwild\updates'); Label='update-state'; Pattern='*.json' }
    )
    foreach($source in $sources) {
      if(-not (Test-Path -LiteralPath $source.Root -PathType Container)) { continue }
      foreach($file in Get-ChildItem -LiteralPath $source.Root -File -Recurse -ErrorAction SilentlyContinue) {
        if($file.Length -gt $maxFileBytes) { continue }
        $relative=$file.FullName.Substring($source.Root.Length).TrimStart('\\','/')
        $dest=Join-Path $stage (Join-Path $source.Label $relative)
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dest) | Out-Null
        Copy-Item -LiteralPath $file.FullName -Destination $dest -Force
        $inventory += [ordered]@{
          source=$file.FullName; bundlePath=(Join-Path $source.Label $relative).Replace('\\','/');
          bytes=$file.Length; modifiedUtc=$file.LastWriteTimeUtc.ToString('o');
          sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $file.FullName).Hash.ToLowerInvariant()
        }
      }
    }
    $gitState='Unavailable'
    if(Get-Command git -ErrorAction SilentlyContinue) {
      Push-Location $Root
      try {
        $old=$ErrorActionPreference; $ErrorActionPreference='Continue'
        try { $gitState=(@(& git status --short --branch 2>&1) -join "`r`n") } finally { $ErrorActionPreference=$old }
      } finally { Pop-Location }
    }
    Set-Content -LiteralPath (Join-Path $stage 'git-state.txt') -Value $gitState -Encoding UTF8
    $environment=[ordered]@{
      schema='havenwild.troubleshooting.environment.v1'; createdUtc=(Get-Date).ToUniversalTime().ToString('o');
      result=$Result; repository=$Root; qualityGateId=$script:QualityGateRunId; pass=(Get-CurrentAcceptedPass);
      powershell=$PSVersionTable.PSVersion.ToString(); os=[Environment]::OSVersion.VersionString;
      editor=(Get-BuildState 'haven_editor_native.exe'); client=(Get-BuildState 'haven_game.exe'); baseline=(Get-BaselineState)
    }
    Write-JsonAtomic -Path (Join-Path $stage 'environment.json') -Value $environment
    Write-JsonAtomic -Path (Join-Path $stage 'diagnostic-index.json') -Value ([ordered]@{
      schema='havenwild.troubleshooting.index.v1'; createdUtc=(Get-Date).ToUniversalTime().ToString('o');
      qualityGateId=$script:QualityGateRunId; result=$Result; fileCount=$inventory.Count; files=$inventory
    })
    $summary=@(
      '# Havenwild Troubleshooting Bundle', '',
      ("- Created: {0:o}" -f (Get-Date)), ("- Result: {0}" -f $Result),
      ("- Quality gate: {0}" -f $script:QualityGateRunId), ("- Files collected: {0}" -f $inventory.Count), '',
      'This escalation bundle contains the available persistent logs plus gate/update state.',
      'Generated binaries, assets, saves, credentials, Git object storage, and oversized files are intentionally excluded.'
    )
    Set-Content -LiteralPath (Join-Path $stage 'TROUBLESHOOTING_SUMMARY.md') -Value $summary -Encoding UTF8
    Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $bundlePath -Force
    Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue
    $hash=(Get-FileHash -Algorithm SHA256 -LiteralPath $bundlePath).Hash.ToLowerInvariant()
    Write-Color ("TROUBLESHOOTING BUNDLE: {0}" -f $bundlePath) Cyan
    Write-Color ("TROUBLESHOOTING SHA-256: {0}" -f $hash) DarkGray
    Write-Color ("TROUBLESHOOTING FILES: {0}" -f $inventory.Count) DarkGray
  } catch {
    Write-Color ("Troubleshooting bundle warning: {0}" -f $_.Exception.Message) Yellow
  }
}

function Complete-QualityGate([string]$Result) {
  if($script:QualityGateFinalized) { return }
  $script:QualityGateFinalized=$true
  try { New-DebugBundle $Result } catch { Write-Color ("Debug bundle finalizer warning: {0}" -f $_.Exception.Message) Yellow }
  if($Result -ne 'PASS') { try { Publish-FailureDebugHandoff $Result } catch { Write-Color ("Failure debug handoff finalizer warning: {0}" -f $_.Exception.Message) Yellow } }
  try { Write-QualityGateRunRecord $Result } catch { Write-Color ("Quality gate record warning: {0}" -f $_.Exception.Message) Yellow }
  $script:QualityGateActive=$false
  Refresh-ArtifactIndex -Quiet
}
function Invoke-FullQualityGate {
  $script:QualityGateRunId=("QG-{0}-{1}" -f (Get-Date -Format 'yyyyMMdd-HHmmss'),[guid]::NewGuid().ToString('N').Substring(0,8))
  $script:QualityGateStarted=Get-Date
  $script:QualityGateActionLogs=@()
  $script:QualityGateActions=@()
  $script:LastDebugBundlePath=$null
  $script:QualityGateFinalized=$false
  $script:QualityGateActive=$true
  Write-Color ("RUN-SCOPED LOG SET: {0}; previous logs are retained." -f $script:QualityGateRunId) DarkGray
  Write-Color 'SEQUENCE Full quality gate (patch intake + root audit + build + tests)' Cyan

  trap {
    $script:LastName='Full quality gate'; $script:LastResult='FAIL'; $script:LastActionExitCode=1
    Write-Color ("FULL QUALITY GATE ABORTED: {0}" -f $_.Exception.Message) Red
    Complete-QualityGate 'ABORTED'
    break
  }

  $controlFingerprintBefore=Get-ControlCenterAuthorityFingerprint
  $patchIntake = Join-Path $PSScriptRoot 'InvokeRootPatchIntake.ps1'
  if(-not (Test-Path -LiteralPath $patchIntake -PathType Leaf)) {
    $script:LastName='Root incremental patch intake'; $script:LastResult='FAIL'; $script:LastActionExitCode=1
    Write-Color ("Sequence stopped: patch intake authority is missing: {0}" -f $patchIntake) Red
    Complete-QualityGate 'FAIL'; return
  }
  $script:CurrentCommandKey='update.root-patch-intake'
  Invoke-HavenwildAction 'Root incremental patch intake' {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $patchIntake -Root $Root
  } 'updates'
  $script:CurrentCommandKey=$null
  if($script:LastResult -ne 'PASS') {
    Write-Color 'Sequence stopped after Root incremental patch intake.' Red
    Complete-QualityGate 'FAIL'; return
  }

  $controlFingerprintAfter=Get-ControlCenterAuthorityFingerprint
  if($controlFingerprintAfter -ne $controlFingerprintBefore) {
    Write-Color 'CONTROL CENTER UPDATED: restarting the Full Quality Gate under the newly applied Control Center source.' Yellow
    Add-Content -LiteralPath $SessionLog -Value ("Control Center authority changed during patch intake: {0} -> {1}. Restarting Full Quality Gate." -f $controlFingerprintBefore,$controlFingerprintAfter)
    $script:QualityGateActive=$false
    $restartArgs=@('-NoProfile','-ExecutionPolicy','Bypass','-File',$PSCommandPath,'-Command','validation.full-quality-gate','-Pass',$Pass)
    if($script:ReturnToInteractiveMenu) { $restartArgs += '-ReturnToMenu' }
    & powershell @restartArgs
    $restartExit=$LASTEXITCODE
    exit $restartExit
  }

  foreach($key in @('audit.root-cleanliness','build.all','test.workspace')) {
    $entry=Get-CommandByKey $key
    if($null -eq $entry) {
      $script:LastResult='FAIL'; $script:LastActionExitCode=1
      Write-Color ("Sequence stopped: required command key is not registered: {0}" -f $key) Red
      Complete-QualityGate 'FAIL'; return
    }
    Invoke-RegisteredCommand $entry
    if($script:LastResult -ne 'PASS') {
      Write-Color ("Sequence stopped after {0}." -f $entry.Label) Red
      Complete-QualityGate 'FAIL'; return
    }
  }
  $script:LastName='Full quality gate'; $script:LastResult='PASS'; $script:LastActionExitCode=0
  Write-Color 'PASS sequence Full quality gate' Green

  # CC8E9-CANONICAL-GREEN-AUTHORITY
  # Full Quality Gate has exactly one post-pass authority. It writes the same
  # canonical record consumed by the header and every protected Git action.
  $script:LastName='Full quality gate'
  $script:LastResult='PASS'
  $script:LastExitCode=0
  $gateAuthority = Join-Path $PSScriptRoot 'HavenwildGateAuthority.py'
  $gatePython = Get-Command python -ErrorAction SilentlyContinue
  if($null -eq $gatePython){ $gatePython = Get-Command py -ErrorAction SilentlyContinue }
  if($null -eq $gatePython -or -not (Test-Path -LiteralPath $gateAuthority)) {
    $script:LastResult='FAIL'; $script:LastExitCode=1
    Write-Color 'FAIL canonical GREEN finalization: HavenwildGateAuthority.py/Python is unavailable.' Red
    New-DebugBundle 'FAIL'
    Publish-FailureDebugHandoff 'FAIL'
    return
  }
  & $gatePython.Source $gateAuthority finalize --root $Root --session-log $SessionLog 2>&1 | ForEach-Object { Write-Host $_; Add-Content -Path $SessionLog -Value $_ }
  if($LASTEXITCODE -ne 0) {
    $script:LastResult='FAIL'; $script:LastExitCode=1
    Write-Color 'FAIL canonical GREEN finalization. Build/tests passed, but publication certification was not written.' Red
    New-DebugBundle 'FAIL'
    Publish-FailureDebugHandoff 'FAIL'
    return
  }
  New-DebugBundle 'PASS'

}
function Complete-FastQualityGate([string]$Result) {
  Write-FastGateRunRecord $Result
  if($Result -ne 'PASS') { Publish-FailureDebugHandoff $Result }
  $script:QualityGateActive=$false
  Refresh-ArtifactIndex -Quiet
}
function Invoke-FastQualityGate {
  $script:QualityGateRunId=("FG-{0}-{1}" -f (Get-Date -Format 'yyyyMMdd-HHmmss'),[guid]::NewGuid().ToString('N').Substring(0,8))
  $script:QualityGateStarted=Get-Date
  $script:QualityGateActionLogs=@()
  $script:QualityGateActions=@()
  $script:QualityGateActive=$true
  Write-Color ("FAST DEVELOPMENT GATE: {0}" -f $script:QualityGateRunId) Cyan
  Write-Color 'Incremental development lane: pending root patches are applied first; the last Full Gate remains the certified baseline.' Yellow

  $controlFingerprintBefore=Get-ControlCenterAuthorityFingerprint
  $patchIntake=Join-Path $PSScriptRoot 'InvokeRootPatchIntake.ps1'
  if(-not (Test-Path -LiteralPath $patchIntake -PathType Leaf)) {
    $script:LastName='Root incremental patch intake'; $script:LastResult='FAIL'; $script:LastActionExitCode=1
    Write-Color ("Fast gate stopped: patch intake authority is missing: {0}" -f $patchIntake) Red
    Complete-FastQualityGate 'FAIL'; return
  }
  $script:CurrentCommandKey='update.root-patch-intake'
  Invoke-HavenwildAction 'Root incremental patch intake' {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $patchIntake -Root $Root
  } 'updates'
  $script:CurrentCommandKey=$null
  if($script:LastResult -ne 'PASS') { Complete-FastQualityGate 'FAIL'; return }

  $controlFingerprintAfter=Get-ControlCenterAuthorityFingerprint
  if($controlFingerprintAfter -ne $controlFingerprintBefore) {
    Write-Color 'CONTROL CENTER UPDATED: restarting the Fast Development Gate under the newly applied Control Center source.' Yellow
    $script:QualityGateActive=$false
    $restartArgs=@('-NoProfile','-ExecutionPolicy','Bypass','-File',$PSCommandPath,'-Command','validation.fast-quality-gate','-Pass',$Pass)
    if($script:ReturnToInteractiveMenu) { $restartArgs += '-ReturnToMenu' }
    & powershell @restartArgs
    $restartExit=$LASTEXITCODE
    exit $restartExit
  }

  foreach($key in @('audit.root-cleanliness','control.self-test','build.check-editor')) {
    $entry=Get-CommandByKey $key
    if($null -eq $entry) {
      $script:LastResult='FAIL'; $script:LastActionExitCode=1
      Write-Color ("Fast gate stopped: required command key is not registered: {0}" -f $key) Red
      Complete-FastQualityGate 'FAIL'; return
    }
    Invoke-RegisteredCommand $entry
    if($script:LastResult -ne 'PASS') { Write-Color ("Fast gate stopped after {0}." -f $entry.Label) Red; Complete-FastQualityGate 'FAIL'; return }
  }
  $script:LastName='Incremental development gate'; $script:LastResult='PASS'; $script:LastActionExitCode=0
  Write-Color 'PASS Incremental Development Gate.' Green
  Write-Color 'Incremental checks PASS. The previous GREEN Full Gate remains the certification baseline until an explicit Full Quality Gate recertifies current source.' Yellow
  Complete-FastQualityGate 'PASS'
}
function Invoke-MenuEntry([hashtable]$Entry) {
  if($null -eq $Entry){ Write-Color 'Unknown command.' Yellow; return }
  if([string]$Entry.Kind -eq 'BuiltinQualityGate') { Invoke-FullQualityGate; return }
  if([string]$Entry.Kind -eq 'BuiltinFastQualityGate') { Invoke-FastQualityGate; return }
  Invoke-RegisteredCommand $Entry
}
function Invoke-SubMenu([string]$MenuKey,[string]$Title) {
  do {
    $entries=@(Get-MenuEntries $MenuKey)
    Show-Header
    Show-SubMenu $Title $entries
    $choice=Read-Host 'Select an option'
    if($choice -eq '0'){ return }
    $index=0
    if([int]::TryParse($choice,[ref]$index) -and $index -ge 1 -and $index -le $entries.Count) {
      $selected=$entries[$index-1]
      Invoke-MenuEntry $selected
      if([string]$selected.Kind -notin @('BuiltinQualityGate','BuiltinFastQualityGate')) {
        Write-Color ''
        Read-Host 'Press Enter to return to the menu' | Out-Null
      }
    } else {
      Write-Color 'Unknown menu option.' Yellow
      Start-Sleep -Milliseconds 650
    }
  } while($true)
}
function Invoke-RegisteredCommand([hashtable]$Entry) {
  if($null -eq $Entry){ Write-Color 'Unknown command.' Yellow; return }
  $name=[string]$Entry.Label; $category=if($Entry.Category){[string]$Entry.Category}else{'sessions'}
  $previousCommandKey=$script:CurrentCommandKey
  $script:CurrentCommandKey=[string]$Entry.Key
  switch([string]$Entry.Kind){
    'BuiltinQualityGate' { Invoke-FullQualityGate }
    'BuiltinFastQualityGate' { Invoke-FastQualityGate }
    'Build' {
      $buildArgs=@($Entry.Args)
      Invoke-HavenwildAction $name { & (Join-Path $Root 'tools\build\Build.cmd') @buildArgs } $category
      if($buildArgs.Count -gt 0 -and $buildArgs[0] -in @('editor','game','devgame')) {
        $sessionResult=if($script:LastResult -eq 'PASS'){'CLEAN'}else{'ABNORMAL_EXIT'}
        New-TroubleshootingBundle $sessionResult
      }
    }
    'Script' {
      $scriptPath=Join-Path $PSScriptRoot ([string]$Entry.Script)
      $commandArgs=@('-Root',$Root)+@($Entry.Args)
      Invoke-HavenwildAction $name {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $scriptPath @commandArgs
      } $category
    }
    'Package' { $mode=[string]$Entry.Mode; Invoke-HavenwildAction $name { & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'PackageProject.ps1') -Root $Root -Mode $mode -Pass $Pass } $category }
    'Dependencies' { Invoke-EnvironmentDoctor }
    'LatestLog' { if(Test-Path $SessionLog){ Start-Process notepad.exe $SessionLog } }
    'Open' { Open-Path (Join-Path $Root ([string]$Entry.Path)) }
    'OpenArtifact' { Open-LatestArtifact ([string]$Entry.Artifact) }
    'ControlSelfTest' { Invoke-ControlCenterSelfTest }
    'EnvironmentDoctor' { Invoke-EnvironmentDoctor }
    'QualityGateHistory' { Invoke-QualityGateHistory }
    'QualityGateCompare' { Invoke-QualityGateComparison }
    'CompilerWarningSummary' { Invoke-CompilerWarningSummary }
    'DebugBundle' { New-DebugBundle 'MANUAL'; Refresh-ArtifactIndex -Quiet; if($script:LastDebugBundlePath){ Reveal-DebugHandoff $script:LastDebugBundlePath }; $script:LastName='Create debug handoff'; $script:LastResult='PASS'; $script:LastActionExitCode=0 }
    'UpdateStatus' { Invoke-UpdateStatus }
    'RecoveryInspect' { Invoke-InspectLatestRecovery }
    'Help' { & (Join-Path $Root 'tools\build\Build.cmd') help; Write-Color 'Project tooling lives under tools\; HavenwildTools.cmd remains the single root Control Center launcher.' DarkGray }
    default { Write-Color ("Unsupported command kind: {0}" -f $Entry.Kind) Yellow }
  }
  $script:CurrentCommandKey=$previousCommandKey
  if($script:LastResult -eq 'FAIL' -and [string]$Entry.Kind -notin @('BuiltinQualityGate','BuiltinFastQualityGate')) {
    Publish-FailureDebugHandoff 'FAIL'
  }
}

Set-Location $Root
Initialize-StandardArtifactFolders
$registryIssues=@(Get-ControlCenterRegistryIssues)
foreach($issue in $registryIssues) { $script:StartupWarnings += ("Control Center registry: {0}" -f $issue) }
Refresh-ArtifactIndex -Quiet
Add-Content $SessionLog ("Havenwild Tools started: {0:o}" -f (Get-Date))
$script:ReturnToInteractiveMenu=[bool]$ReturnToMenu
if(-not $script:ReturnToInteractiveMenu -and (Test-ControlCenterRestartChild)) {
  $script:ReturnToInteractiveMenu=$true
  Add-Content $SessionLog 'Detected nested Control Center self-update child; interactive menu ownership will be preserved.'
}
if($Command -ne 'menu'){
  Invoke-RegisteredCommand (Get-CommandById $Command)
  if(-not $script:ReturnToInteractiveMenu) {
    exit $script:LastActionExitCode
  }
  Write-Color ''
  Write-Color 'CONTROL CENTER HANDOFF COMPLETE: continuing in the updated interactive menu.' Green
}
do {
  Show-Header
  Show-MainMenu
  $choice=Read-Host 'Select an option'
  # `break` inside a PowerShell switch exits only the switch, not this outer
  # interactive loop. Handle Exit before dispatch so main-menu 0 terminates
  # both ordinary and self-update-owned Control Center sessions cleanly.
  if($choice -eq '0') { break }
  switch($choice) {
    '1' { Invoke-FullQualityGate }
    '2' { Invoke-RootGreenPublication; Write-Color ''; Read-Host 'Press Enter to return to the menu' | Out-Null }
    '3' { Invoke-SubMenu 'build' 'Build & Verify' }
    '4' { Invoke-SubMenu 'run' 'Run & Play' }
    '5' { Invoke-SubMenu 'world' 'World, Terrain & Scene Tools' }
    '6' { Invoke-SubMenu 'assets' 'Asset Authority & Catalog' }
    '7' { Invoke-SubMenu 'project' 'Project Maintenance & Diagnostics' }
    '8' { Invoke-SubMenu 'package' 'Packaging & Baselines' }
    '9' { Invoke-SubMenu 'logs' 'Logs & Help' }
    '10' { Invoke-SubMenu 'advanced' 'Advanced / All Registered Commands' }
    '11' { Invoke-GitHubMenu }
    default { Write-Color 'Unknown menu option.' Yellow; Start-Sleep -Milliseconds 650 }
  }
} while($true)
Write-Color 'Havenwild Tools closed.' DarkGray
exit 0
