[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$Root,
  [ValidateSet('Preview','Restore')][string]$Mode='Preview'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0
Add-Type -AssemblyName System.IO.Compression.FileSystem

$rootResolved = (Resolve-Path -LiteralPath $Root).Path
$rootFull = [IO.Path]::GetFullPath($rootResolved).TrimEnd([char[]]'\/')
$rootPrefix = $rootFull + [IO.Path]::DirectorySeparatorChar
$updateRoot = Join-Path $rootFull '.havenwild\updates'
$backupRoot = Join-Path $updateRoot 'backups'
$restoreStageRoot = Join-Path $updateRoot 'restore-staging'
$historyRoot = Join-Path $updateRoot 'history'
$lastAppliedPath = Join-Path $updateRoot 'last-applied.json'
$lastUndoPath = Join-Path $updateRoot 'last-undo.json'
$appliedRoot = Join-Path $rootFull 'artifacts\updates\applied'
$undoneRoot = Join-Path $rootFull 'artifacts\updates\undone'
$greenGateMarker = Join-Path $rootFull '.havenwild\last-green-quality-gate.json'
$recoveryTool = Join-Path $rootFull 'tools\control\CreateRecoveryRollup.ps1'
New-Item -ItemType Directory -Force -Path $backupRoot,$restoreStageRoot,$historyRoot,$appliedRoot,$undoneRoot | Out-Null

function Test-SafeRelativePath {
  param([Parameter(Mandatory=$true)][string]$Relative)
  if([string]::IsNullOrWhiteSpace($Relative)){ return $false }
  $normalized = $Relative.Replace('/', '\')
  if($normalized.StartsWith('\') -or $normalized.StartsWith('/')){ return $false }
  if($normalized -match '^[A-Za-z]:'){ return $false }
  if($normalized.Contains(':')){ return $false }
  if($normalized -match '(^|[\\/])\.\.([\\/]|$)'){ return $false }
  if($normalized.IndexOf([char]0) -ge 0){ return $false }
  $candidate = [IO.Path]::GetFullPath((Join-Path $rootFull $normalized))
  if($candidate.Equals($rootFull,[StringComparison]::OrdinalIgnoreCase)){ return $false }
  return $candidate.StartsWith($rootPrefix,[StringComparison]::OrdinalIgnoreCase)
}

function Get-SafeDestinationPath {
  param([Parameter(Mandatory=$true)][string]$Relative)
  if(-not (Test-SafeRelativePath -Relative $Relative)){ throw "Unsafe restore path: $Relative" }
  return [IO.Path]::GetFullPath((Join-Path $rootFull ($Relative.Replace('/', '\'))))
}

function Copy-WithParent {
  param([Parameter(Mandatory=$true)][string]$Source,[Parameter(Mandatory=$true)][string]$Destination)
  $parent = Split-Path -Parent $Destination
  if(-not (Test-Path -LiteralPath $parent -PathType Container)){ New-Item -ItemType Directory -Force -Path $parent | Out-Null }
  Copy-Item -LiteralPath $Source -Destination $Destination -Force
}

function Read-PatchManifest {
  param([Parameter(Mandatory=$true)][string]$ZipPath)
  $archive=[IO.Compression.ZipFile]::OpenRead($ZipPath)
  try {
    $entry=$archive.Entries | Where-Object { $_.FullName -eq 'PATCH_MANIFEST.json' } | Select-Object -First 1
    if($null -eq $entry){ throw "PATCH_MANIFEST.json is missing from $ZipPath" }
    $reader=New-Object IO.StreamReader($entry.Open(),[Text.Encoding]::UTF8,$true)
    try { $manifest=$reader.ReadToEnd() | ConvertFrom-Json } finally { $reader.Dispose() }
  } finally { $archive.Dispose() }
  if([string]$manifest.schema -ne 'havenwild.root_patch.v1'){ throw "Unsupported patch schema: $($manifest.schema)" }
  if([string]$manifest.project -ne 'Havenwild'){ throw "Patch project mismatch: $($manifest.project)" }
  return $manifest
}

function Resolve-ArchivedZip {
  param($State)
  foreach($propertyName in @('archivedZip','archive')) {
    $property=$State.PSObject.Properties[$propertyName]
    if($null -ne $property -and -not [string]::IsNullOrWhiteSpace([string]$property.Value)) {
      $candidate=[string]$property.Value
      if(Test-Path -LiteralPath $candidate -PathType Leaf){ return (Resolve-Path -LiteralPath $candidate).Path }
    }
  }
  $patchId=[string]$State.patchId
  $hits=@(Get-ChildItem -LiteralPath $appliedRoot -File -Recurse -Filter '*.zip' -ErrorAction SilentlyContinue | Sort-Object LastWriteTimeUtc -Descending)
  foreach($hit in $hits) {
    try {
      $m=Read-PatchManifest -ZipPath $hit.FullName
      if([string]$m.patchId -eq $patchId){ return $hit.FullName }
    } catch {}
  }
  throw "Could not locate archived ZIP for last applied patch: $patchId"
}

function Resolve-BackupSnapshot {
  param($State,[string]$ArchivedZip)
  $backupProperty=$State.PSObject.Properties['backupSnapshot']
  if($null -ne $backupProperty -and -not [string]::IsNullOrWhiteSpace([string]$backupProperty.Value)) {
    $candidate=[string]$backupProperty.Value
    if(Test-Path -LiteralPath $candidate -PathType Container){ return (Resolve-Path -LiteralPath $candidate).Path }
  }
  $safeBaseName=[IO.Path]::GetFileNameWithoutExtension($ArchivedZip) -replace '[^A-Za-z0-9._-]','_'
  $candidate=Get-ChildItem -LiteralPath $backupRoot -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like "*-$safeBaseName" } |
    Sort-Object LastWriteTimeUtc -Descending |
    Select-Object -First 1
  if($null -eq $candidate){ throw "Could not locate transactional backup snapshot for $safeBaseName" }
  return $candidate.FullName
}

function Get-PassFromManifest {
  param($Manifest)
  $passProperty=$Manifest.PSObject.Properties['pass']
  if($null -ne $passProperty -and -not [string]::IsNullOrWhiteSpace([string]$passProperty.Value)){ return [string]$passProperty.Value }
  $value=[string]$Manifest.patchId
  if($value.StartsWith('Pass',[StringComparison]::OrdinalIgnoreCase)){ $value=$value.Substring(4) }
  $dash=$value.IndexOf('-')
  if($dash -gt 0){ $value=$value.Substring(0,$dash) }
  return $value
}

function Write-PreviousLastAppliedState {
  param([string]$ExcludeZip)
  $previous=Get-ChildItem -LiteralPath $appliedRoot -File -Recurse -Filter '*.zip' -ErrorAction SilentlyContinue |
    Where-Object { -not $_.FullName.Equals($ExcludeZip,[StringComparison]::OrdinalIgnoreCase) } |
    Sort-Object LastWriteTimeUtc -Descending |
    Select-Object -First 1
  if($null -eq $previous){
    Remove-Item -LiteralPath $lastAppliedPath -Force -ErrorAction SilentlyContinue
    return
  }
  try {
    $manifest=Read-PatchManifest -ZipPath $previous.FullName
    $payload=[ordered]@{
      schema='havenwild.last_applied_patch.v1'
      project='Havenwild'
      patchId=[string]$manifest.patchId
      pass=Get-PassFromManifest $manifest
      appliedUtc=$previous.LastWriteTimeUtc.ToString('o')
      archivedZip=$previous.FullName
      archive=$previous.FullName
      files=@($manifest.files).Count
      removals=@($manifest.remove).Count
      reconstructedAfterUndo=$true
    }
    $payload | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $lastAppliedPath -Encoding UTF8
  } catch {
    Remove-Item -LiteralPath $lastAppliedPath -Force -ErrorAction SilentlyContinue
  }
}

if(-not (Test-Path -LiteralPath $lastAppliedPath -PathType Leaf)){ throw 'No last-applied root patch state exists to inspect or undo.' }
$state=Get-Content -LiteralPath $lastAppliedPath -Raw | ConvertFrom-Json
$archivedZip=Resolve-ArchivedZip -State $state
$manifest=Read-PatchManifest -ZipPath $archivedZip
if([string]$manifest.patchId -ne [string]$state.patchId){ throw 'last-applied state does not match the archived patch manifest.' }
$backup=Resolve-BackupSnapshot -State $state -ArchivedZip $archivedZip
$newFileLedger=Join-Path $backup '_new_files.txt'
$newFiles=@{}
if(Test-Path -LiteralPath $newFileLedger -PathType Leaf){
  foreach($line in Get-Content -LiteralPath $newFileLedger){
    if([string]::IsNullOrWhiteSpace($line)){ continue }
    $normalized=$line.Replace('\','/').Trim()
    if(-not (Test-SafeRelativePath -Relative $normalized)){ throw "Unsafe new-file ledger path: $normalized" }
    $newFiles[$normalized.ToLowerInvariant()]=$true
  }
}

$files=@($manifest.files)
$removals=@($manifest.remove)
$issues=@()
$restoreCount=0
$deleteCount=0
$reviveCount=0
foreach($file in $files){
  $relative=[string]$file.path
  if(-not (Test-SafeRelativePath -Relative $relative)){ $issues += "unsafe manifest path: $relative"; continue }
  $destination=Get-SafeDestinationPath -Relative $relative
  if(-not (Test-Path -LiteralPath $destination -PathType Leaf)){ $issues += "current patched file is missing: $relative"; continue }
  $actual=(Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant()
  $expected=([string]$file.sha256).ToLowerInvariant()
  if($actual -ne $expected){ $issues += "current file changed since patch apply: $relative"; continue }
  if($newFiles.ContainsKey($relative.ToLowerInvariant())) {
    $deleteCount++
  } else {
    $backupPath=Join-Path $backup ($relative.Replace('/','\'))
    if(-not (Test-Path -LiteralPath $backupPath -PathType Leaf)){ $issues += "pre-patch backup is missing: $relative" }
    else { $restoreCount++ }
  }
}
foreach($relativeObject in $removals){
  $relative=[string]$relativeObject
  if(-not (Test-SafeRelativePath -Relative $relative)){ $issues += "unsafe removal path: $relative"; continue }
  $destination=Get-SafeDestinationPath -Relative $relative
  if(Test-Path -LiteralPath $destination){ $issues += "removed path exists again, so the tree changed after patch apply: $relative"; continue }
  $backupPath=Join-Path $backup ($relative.Replace('/','\'))
  if(Test-Path -LiteralPath $backupPath -PathType Leaf){ $reviveCount++ }
}

Write-Host ("PATCH: {0}" -f $manifest.patchId)
Write-Host ("PASS: {0}" -f (Get-PassFromManifest $manifest))
Write-Host ("ARCHIVE: {0}" -f $archivedZip)
Write-Host ("BACKUP: {0}" -f $backup)
Write-Host ("RESTORE EXISTING FILES: {0}" -f $restoreCount)
Write-Host ("DELETE PATCH-CREATED FILES: {0}" -f $deleteCount)
Write-Host ("REVIVE PATCH-REMOVED FILES: {0}" -f $reviveCount)

if($issues.Count -gt 0){
  foreach($issue in $issues){ Write-Host ("BLOCKED: {0}" -f $issue) }
  throw ("Undo validation failed with {0} issue(s). No files were changed." -f $issues.Count)
}
Write-Host 'PASS: current repository still matches the exact post-patch state for every path the patch touched.'
if($Mode -eq 'Preview'){
  Write-Host 'PREVIEW ONLY: no repository files were changed.'
  exit 0
}

if(-not (Test-Path -LiteralPath $recoveryTool -PathType Leaf)){ throw "Recovery rollup helper is missing: $recoveryTool" }
$confirmation=Read-Host ("Type UNDO to restore the pre-patch snapshot for {0}" -f $manifest.patchId)
if($confirmation -cne 'UNDO'){ throw 'Undo cancelled. Confirmation token did not match UNDO.' }

Write-Host 'Creating a recovery rollup before undo...'
& powershell -NoProfile -ExecutionPolicy Bypass -File $recoveryTool -Root $rootFull
if($LASTEXITCODE -ne 0){ throw "Recovery rollup creation failed with exit code $LASTEXITCODE. Undo was not started." }
$recoveryPointer=Join-Path $rootFull 'artifacts\recovery\LATEST_RECOVERY_ROLLUP.txt'
$recoveryZip=$null
if(Test-Path -LiteralPath $recoveryPointer -PathType Leaf){
  foreach($line in Get-Content -LiteralPath $recoveryPointer){ if($line -match '^ZIP=(.+)$'){ $recoveryZip=$Matches[1].Trim() } }
}

$stamp=Get-Date -Format 'yyyyMMdd-HHmmss'
$stage=Join-Path $restoreStageRoot ("{0}-{1}" -f $stamp,[guid]::NewGuid().ToString('N'))
$stageFiles=Join-Path $stage 'current'
$absentLedger=Join-Path $stage '_absent_before_restore.txt'
New-Item -ItemType Directory -Force -Path $stageFiles | Out-Null
$affected=@()
foreach($file in $files){ $affected += [string]$file.path }
foreach($relativeObject in $removals){ $affected += [string]$relativeObject }
$affected=@($affected | Select-Object -Unique)
$absent=@()
foreach($relative in $affected){
  $destination=Get-SafeDestinationPath -Relative $relative
  if(Test-Path -LiteralPath $destination -PathType Leaf){ Copy-WithParent -Source $destination -Destination (Join-Path $stageFiles ($relative.Replace('/','\'))) }
  else { $absent += $relative }
}
if($absent.Count -gt 0){ Set-Content -LiteralPath $absentLedger -Value $absent -Encoding UTF8 }

$restoreStarted=$false
try {
  $restoreStarted=$true
  foreach($file in $files){
    $relative=[string]$file.path
    $destination=Get-SafeDestinationPath -Relative $relative
    if($newFiles.ContainsKey($relative.ToLowerInvariant())) {
      if(Test-Path -LiteralPath $destination -PathType Leaf){ Remove-Item -LiteralPath $destination -Force }
    } else {
      $backupPath=Join-Path $backup ($relative.Replace('/','\'))
      Copy-WithParent -Source $backupPath -Destination $destination
    }
  }
  foreach($relativeObject in $removals){
    $relative=[string]$relativeObject
    $destination=Get-SafeDestinationPath -Relative $relative
    $backupPath=Join-Path $backup ($relative.Replace('/','\'))
    if(Test-Path -LiteralPath $backupPath -PathType Leaf){ Copy-WithParent -Source $backupPath -Destination $destination }
    elseif(Test-Path -LiteralPath $destination -PathType Leaf){ Remove-Item -LiteralPath $destination -Force }
  }

  foreach($file in $files){
    $relative=[string]$file.path
    $destination=Get-SafeDestinationPath -Relative $relative
    if($newFiles.ContainsKey($relative.ToLowerInvariant())) {
      if(Test-Path -LiteralPath $destination){ throw "Post-undo assertion failed; patch-created path still exists: $relative" }
    } else {
      $backupPath=Join-Path $backup ($relative.Replace('/','\'))
      $expected=(Get-FileHash -LiteralPath $backupPath -Algorithm SHA256).Hash.ToLowerInvariant()
      if(-not (Test-Path -LiteralPath $destination -PathType Leaf)){ throw "Post-undo restored file missing: $relative" }
      $actual=(Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant()
      if($actual -ne $expected){ throw "Post-undo SHA-256 mismatch: $relative" }
    }
  }
  foreach($relativeObject in $removals){
    $relative=[string]$relativeObject
    $destination=Get-SafeDestinationPath -Relative $relative
    $backupPath=Join-Path $backup ($relative.Replace('/','\'))
    if(Test-Path -LiteralPath $backupPath -PathType Leaf){
      $expected=(Get-FileHash -LiteralPath $backupPath -Algorithm SHA256).Hash.ToLowerInvariant()
      if(-not (Test-Path -LiteralPath $destination -PathType Leaf)){ throw "Post-undo revived file missing: $relative" }
      $actual=(Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant()
      if($actual -ne $expected){ throw "Post-undo revived file hash mismatch: $relative" }
    } elseif(Test-Path -LiteralPath $destination){ throw "Post-undo path should remain absent: $relative" }
  }

  $undoArchiveDir=Join-Path $undoneRoot $stamp
  New-Item -ItemType Directory -Force -Path $undoArchiveDir | Out-Null
  $undoArchiveZip=Join-Path $undoArchiveDir ([IO.Path]::GetFileName($archivedZip))
  Move-Item -LiteralPath $archivedZip -Destination $undoArchiveZip -Force
  foreach($sidecar in @("$archivedZip.sha256","$archivedZip.sha256.txt")){
    if(Test-Path -LiteralPath $sidecar -PathType Leaf){ Move-Item -LiteralPath $sidecar -Destination (Join-Path $undoArchiveDir ([IO.Path]::GetFileName($sidecar))) -Force }
  }

  $undoState=[ordered]@{
    schema='havenwild.patch_undo.v1'
    project='Havenwild'
    patchId=[string]$manifest.patchId
    pass=Get-PassFromManifest $manifest
    undoneUtc=(Get-Date).ToUniversalTime().ToString('o')
    backupSnapshot=$backup
    recoveryRollup=$recoveryZip
    archivedZip=$undoArchiveZip
    restoredFiles=$restoreCount
    deletedPatchCreatedFiles=$deleteCount
    revivedRemovedFiles=$reviveCount
  }
  $undoState | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $lastUndoPath -Encoding UTF8
  $historyPath=Join-Path $historyRoot ("{0}-undo-{1}.json" -f $stamp,(([string]$manifest.patchId) -replace '[^A-Za-z0-9._-]','_'))
  $undoState | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $historyPath -Encoding UTF8
  Write-PreviousLastAppliedState -ExcludeZip $archivedZip
  Remove-Item -LiteralPath $greenGateMarker -Force -ErrorAction SilentlyContinue
  Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue
  Write-Host ("UNDO COMPLETE: {0}" -f $manifest.patchId)
  Write-Host ("RECOVERY ROLLUP: {0}" -f $recoveryZip)
  Write-Host 'GREEN GATE INVALIDATED: run Full Quality Gate before treating this restored tree as verified.'
  exit 0
} catch {
  $failure=$_.Exception.Message
  Write-Host ("UNDO FAILED: {0}" -f $failure)
  if($restoreStarted){
    Write-Host 'ROLLBACK: restoring the repository state captured immediately before undo.'
    $absentBefore=@{}
    if(Test-Path -LiteralPath $absentLedger -PathType Leaf){ foreach($line in Get-Content -LiteralPath $absentLedger){ if(-not [string]::IsNullOrWhiteSpace($line)){ $absentBefore[$line.Replace('\','/').ToLowerInvariant()]=$true } } }
    foreach($relative in $affected){
      $destination=Get-SafeDestinationPath -Relative $relative
      $staged=Join-Path $stageFiles ($relative.Replace('/','\'))
      if(Test-Path -LiteralPath $staged -PathType Leaf){ Copy-WithParent -Source $staged -Destination $destination }
      elseif($absentBefore.ContainsKey($relative.ToLowerInvariant()) -and (Test-Path -LiteralPath $destination -PathType Leaf)){ Remove-Item -LiteralPath $destination -Force -ErrorAction SilentlyContinue }
    }
    Write-Host 'ROLLBACK: complete.'
  }
  throw $failure
}
