[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$Root,
  [switch]$Prompt
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$rootResolved = (Resolve-Path -LiteralPath $Root).Path
$rootFull = [IO.Path]::GetFullPath($rootResolved).TrimEnd([char[]]'\/')
$rootPrefix = $rootFull + [IO.Path]::DirectorySeparatorChar
$updateRoot = Join-Path $rootFull '.havenwild\updates'
$stagingRoot = Join-Path $updateRoot 'staging'
$backupRoot = Join-Path $updateRoot 'backups'
$appliedRoot = Join-Path $rootFull 'artifacts\updates\applied'
$failedRoot = Join-Path $rootFull 'artifacts\updates\failed'
$logRoot = Join-Path $rootFull 'logs\updates'
$lastAppliedPath = Join-Path $updateRoot 'last-applied.json'
New-Item -ItemType Directory -Force -Path $stagingRoot,$backupRoot,$appliedRoot,$failedRoot,$logRoot | Out-Null

Add-Type -AssemblyName System.IO.Compression.FileSystem

function Write-UpdateLog {
  param([string]$Path,[string]$Message)
  $line = '[{0}] {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Message
  Write-Host $line
  Add-Content -LiteralPath $Path -Value $line
}

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
  if(-not (Test-SafeRelativePath -Relative $Relative)){
    throw "Unsafe patch path: $Relative"
  }
  return [IO.Path]::GetFullPath((Join-Path $rootFull ($Relative.Replace('/', '\'))))
}

function Get-ArchiveManifestText {
  param([Parameter(Mandatory=$true)][System.IO.Compression.ZipArchive]$Archive)
  $manifestEntries = @($Archive.Entries | Where-Object { $_.FullName.Replace('\','/') -ieq 'PATCH_MANIFEST.json' })
  if($manifestEntries.Count -ne 1){
    throw "Patch must contain exactly one root PATCH_MANIFEST.json; found $($manifestEntries.Count)."
  }
  $reader = New-Object IO.StreamReader($manifestEntries[0].Open(), [Text.Encoding]::UTF8, $true)
  try { return $reader.ReadToEnd() } finally { $reader.Dispose() }
}

function Assert-ZipEntrySafe {
  param([Parameter(Mandatory=$true)][string]$EntryName)
  if([string]::IsNullOrWhiteSpace($EntryName)){ return }
  $normalized = $EntryName.Replace('\','/')
  if($normalized.StartsWith('/') -or $normalized -match '^[A-Za-z]:'){
    throw "Unsafe archive entry: $EntryName"
  }
  if($normalized -match '(^|/)\.\.(/|$)'){
    throw "Traversal archive entry rejected: $EntryName"
  }
}

function Copy-WithParent {
  param([Parameter(Mandatory=$true)][string]$Source,[Parameter(Mandatory=$true)][string]$Destination)
  $parent = Split-Path -Parent $Destination
  if($parent){ New-Item -ItemType Directory -Force -Path $parent | Out-Null }
  Copy-Item -LiteralPath $Source -Destination $Destination -Force
}


function Get-PatchSidecarPath {
  param([Parameter(Mandatory=$true)][string]$ZipPath)
  foreach($candidate in @("$ZipPath.sha256", "$ZipPath.sha256.txt")){
    if(Test-Path -LiteralPath $candidate -PathType Leaf){ return $candidate }
  }
  return $null
}

function Move-PatchTransport {
  param(
    [Parameter(Mandatory=$true)][string]$ZipPath,
    [Parameter(Mandatory=$true)][string]$DestinationRoot,
    [Parameter(Mandatory=$true)][string]$Stamp
  )
  $destDir = Join-Path $DestinationRoot $Stamp
  New-Item -ItemType Directory -Force -Path $destDir | Out-Null
  $zipName = Split-Path -Leaf $ZipPath
  $destZip = Join-Path $destDir $zipName
  if(Test-Path -LiteralPath $destZip){ Remove-Item -LiteralPath $destZip -Force }
  Move-Item -LiteralPath $ZipPath -Destination $destZip -Force
  $sidecar = Get-PatchSidecarPath -ZipPath $ZipPath
  if($sidecar){
    $destSidecar = Join-Path $destDir (Split-Path -Leaf $sidecar)
    if(Test-Path -LiteralPath $destSidecar){ Remove-Item -LiteralPath $destSidecar -Force }
    Move-Item -LiteralPath $sidecar -Destination $destSidecar -Force
  }
  return $destZip
}

function Test-ZipSidecarHash {
  param([Parameter(Mandatory=$true)][string]$ZipPath)
  $sidecar = Get-PatchSidecarPath -ZipPath $ZipPath
  if(-not $sidecar){ return }
  $text = (Get-Content -LiteralPath $sidecar -Raw).Trim()
  if($text -notmatch '(?i)^([a-f0-9]{64})(?:\s+\*?.+)?$'){
    throw "Malformed SHA-256 sidecar: $(Split-Path -Leaf $sidecar)"
  }
  $expected = $Matches[1].ToLowerInvariant()
  $actual = (Get-FileHash -LiteralPath $ZipPath -Algorithm SHA256).Hash.ToLowerInvariant()
  if($actual -ne $expected){ throw "ZIP SHA-256 mismatch for $(Split-Path -Leaf $ZipPath)." }
}


function Test-PatchTransportIsZip {
  param([Parameter(Mandatory=$true)][string]$Path)
  $stream = [IO.File]::OpenRead($Path)
  try {
    if($stream.Length -lt 4){ return $false }
    $bytes = New-Object byte[] 4
    $read = $stream.Read($bytes,0,4)
    if($read -lt 4){ return $false }
    return ($bytes[0] -eq 0x50 -and $bytes[1] -eq 0x4B)
  } finally {
    $stream.Dispose()
  }
}

function Confirm-PatchTransportApply {
  param([Parameter(Mandatory=$true)][IO.FileInfo]$Patch)
  if(-not [bool]$Prompt){ return $true }
  $answer = Read-Host ("Apply pending root patch {0}? [y/N]" -f $Patch.Name)
  return ($answer -match '^[Yy]')
}

function Get-PatchIdFromName {
  param([Parameter(Mandatory=$true)][string]$Name)
  $base = [IO.Path]::GetFileNameWithoutExtension($Name)
  if([string]::IsNullOrWhiteSpace($base)){ return 'manual' }
  return ($base -replace '[^A-Za-z0-9._-]','_')
}

function Assert-GitUnifiedDiffSafe {
  param([Parameter(Mandatory=$true)][string]$PatchText)
  if($PatchText -match '(?m)^GIT binary patch'){
    throw 'Git binary patches are not supported by internal PCC root intake.'
  }
  $sawPath = $false
  foreach($line in ($PatchText -split "`r?`n")){
    if($line -match '^diff --git\s+a/(.+?)\s+b/(.+)$'){
      foreach($relative in @($Matches[1], $Matches[2])){
        if($relative -ne '/dev/null' -and -not (Test-SafeRelativePath -Relative $relative)){
          throw "Unsafe Git patch path: $relative"
        }
      }
      $sawPath = $true
      continue
    }
    if($line -match '^(---|\+\+\+)\s+(a/|b/)?(.+)$'){
      $relative = $Matches[3]
      if($relative -ne '/dev/null' -and -not (Test-SafeRelativePath -Relative $relative)){
        throw "Unsafe Git patch path: $relative"
      }
      $sawPath = $true
    }
  }
  if(-not $sawPath){ throw 'Git unified diff did not declare any file paths.' }
}

function Invoke-GitUnifiedDiffPatch {
  param(
    [Parameter(Mandatory=$true)][IO.FileInfo]$Patch,
    [Parameter(Mandatory=$true)][string]$LogPath,
    [Parameter(Mandatory=$true)][string]$Stamp
  )

  if(-not (Get-Command git -ErrorAction SilentlyContinue)){
    throw 'Git unified-diff patch requires git on PATH.'
  }
  $patchText = Get-Content -LiteralPath $Patch.FullName -Raw -ErrorAction Stop
  if($patchText -notmatch '(?m)^diff --git\s+a/' -or $patchText -notmatch '(?m)^@@'){
    throw "Text patch is not a Git unified diff transport: $($Patch.Name)"
  }
  Assert-GitUnifiedDiffSafe -PatchText $patchText
  $patchId = Get-PatchIdFromName -Name $Patch.Name
  Push-Location $rootFull
  try {
    $check = @(& git apply --check --whitespace=nowarn $Patch.FullName 2>&1)
    if($LASTEXITCODE -ne 0){
      $reverse = @(& git apply --reverse --check --whitespace=nowarn $Patch.FullName 2>&1)
      if($LASTEXITCODE -eq 0){
        Write-UpdateLog $LogPath ("ALREADY APPLIED: {0}" -f $patchId)
        $archivedAlready = Move-PatchTransport -ZipPath $Patch.FullName -DestinationRoot $appliedRoot -Stamp $Stamp
        $lastAppliedAlready = [ordered]@{
          schema = 'havenwild.last_applied_patch.v1'
          project = 'Havenwild'
          patchId = $patchId
          pass = $patchId
          appliedUtc = (Get-Date).ToUniversalTime().ToString('o')
          archivedZip = $archivedAlready
          files = 0
          removals = 0
          applyMode = 'git-unified-diff'
          alreadyApplied = $true
        }
        $lastAppliedAlready | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $lastAppliedPath -Encoding UTF8
        return
      }
      throw ("git apply --check failed for {0}: {1}" -f $Patch.Name, (($check + $reverse) -join ' | '))
    }
    $apply = @(& git apply --whitespace=nowarn $Patch.FullName 2>&1)
    if($LASTEXITCODE -ne 0){
      throw ("git apply failed for {0}: {1}" -f $Patch.Name, ($apply -join ' | '))
    }
  } finally {
    Pop-Location
  }

  $archived = Move-PatchTransport -ZipPath $Patch.FullName -DestinationRoot $appliedRoot -Stamp $Stamp
  $lastApplied = [ordered]@{
    schema = 'havenwild.last_applied_patch.v1'
    project = 'Havenwild'
    patchId = $patchId
    pass = $patchId
    appliedUtc = (Get-Date).ToUniversalTime().ToString('o')
    archivedZip = $archived
    files = $null
    removals = 0
    applyMode = 'git-unified-diff'
  }
  $lastApplied | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $lastAppliedPath -Encoding UTF8
  Write-UpdateLog $LogPath ("APPLIED GIT PATCH: {0}" -f $patchId)
  Write-UpdateLog $LogPath ("ARCHIVED: {0}" -f $archived)
}

function Invoke-OnePatch {
  param([Parameter(Mandatory=$true)][IO.FileInfo]$Patch)

  $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
  $safeBaseName = [IO.Path]::GetFileNameWithoutExtension($Patch.Name) -replace '[^A-Za-z0-9._-]','_'
  $logPath = Join-Path $logRoot ("patch-intake-{0}-{1}.log" -f $stamp,$safeBaseName)
  $stage = Join-Path $stagingRoot ("{0}-{1}" -f $stamp,[guid]::NewGuid().ToString('N'))
  $backup = Join-Path $backupRoot ("{0}-{1}" -f $stamp,$safeBaseName)
  $newFileLedger = Join-Path $backup '_new_files.txt'
  $rollbackNeeded = $false
  $manifest = $null

  New-Item -ItemType Directory -Force -Path $backup | Out-Null
  try {
    Write-UpdateLog $logPath ("PATCH DETECTED: {0}" -f $Patch.Name)
    if(-not (Confirm-PatchTransportApply -Patch $Patch)){
      Write-UpdateLog $logPath ("SKIPPED BY USER: {0}; patch remains in root for later." -f $Patch.Name)
      return
    }
    Test-ZipSidecarHash -ZipPath $Patch.FullName

    if(-not (Test-PatchTransportIsZip -Path $Patch.FullName)){
      Invoke-GitUnifiedDiffPatch -Patch $Patch -LogPath $logPath -Stamp $stamp
      return
    }

    $archive = [IO.Compression.ZipFile]::OpenRead($Patch.FullName)
    try {
      foreach($entry in $archive.Entries){ Assert-ZipEntrySafe -EntryName $entry.FullName }
      $manifestText = Get-ArchiveManifestText -Archive $archive
      try { $manifest = $manifestText | ConvertFrom-Json } catch { throw 'PATCH_MANIFEST.json is not valid JSON.' }

      if(([string]$manifest.schema) -ne 'havenwild.root_patch.v1'){ throw "Unsupported patch schema: $($manifest.schema)" }
      if(([string]$manifest.project) -ne 'Havenwild'){ throw "Patch project mismatch: $($manifest.project)" }
      if(([string]$manifest.applyMode) -ne 'overwrite'){ throw "Unsupported apply mode: $($manifest.applyMode)" }
      if([string]::IsNullOrWhiteSpace([string]$manifest.patchId)){ throw 'Patch manifest is missing patchId.' }

      # `pass` was added after the original root-patch schema. Older/externally
      # generated valid patches may therefore omit it. Resolve it once here and
      # never dereference a missing JSON property during post-apply bookkeeping.
      $manifestPass = ''
      $passProperty = $manifest.PSObject.Properties['pass']
      if($null -ne $passProperty){
        $manifestPass = [string]$passProperty.Value
      }
      if([string]::IsNullOrWhiteSpace($manifestPass)){
        $manifestPass = [string]$manifest.patchId
        if($manifestPass.StartsWith('Pass',[System.StringComparison]::OrdinalIgnoreCase)){
          $manifestPass = $manifestPass.Substring(4)
        }
        $dashIndex = $manifestPass.IndexOf('-')
        if($dashIndex -gt 0){ $manifestPass = $manifestPass.Substring(0,$dashIndex) }
      }
      if([string]::IsNullOrWhiteSpace($manifestPass)){
        throw 'Patch manifest pass could not be resolved from pass or patchId.'
      }

      $manifestFiles = @($manifest.files)
      $manifestPaths = @{}
      foreach($file in $manifestFiles){
        $relative = [string]$file.path
        if(-not (Test-SafeRelativePath -Relative $relative)){ throw "Unsafe manifest file path: $relative" }
        if($relative -ieq 'PATCH_MANIFEST.json'){ throw 'PATCH_MANIFEST.json cannot be a payload file.' }
        if($manifestPaths.ContainsKey($relative.ToLowerInvariant())){ throw "Duplicate manifest path: $relative" }
        if(([string]$file.sha256) -notmatch '(?i)^[a-f0-9]{64}$'){ throw "Invalid SHA-256 for $relative" }
        $manifestPaths[$relative.ToLowerInvariant()] = $file
      }

      $removals = @($manifest.remove)
      if($manifestFiles.Count -eq 0 -and $removals.Count -eq 0){
        throw 'Patch manifest contains no payload files or removals.'
      }
      foreach($relativeObject in $removals){
        $relative = [string]$relativeObject
        if(-not (Test-SafeRelativePath -Relative $relative)){ throw "Unsafe removal path: $relative" }
        if($manifestPaths.ContainsKey($relative.ToLowerInvariant())){ throw "Path cannot be both overwritten and removed: $relative" }
      }

      [IO.Compression.ZipFile]::ExtractToDirectory($Patch.FullName,$stage)
    } finally {
      $archive.Dispose()
    }

    $stageManifest = Join-Path $stage 'PATCH_MANIFEST.json'
    if(Test-Path -LiteralPath $stageManifest){ Remove-Item -LiteralPath $stageManifest -Force }

    $actualPayload = @()
    foreach($file in Get-ChildItem -LiteralPath $stage -File -Recurse){
      $relative = $file.FullName.Substring($stage.Length).TrimStart([char[]]'\/').Replace('\','/')
      $actualPayload += $relative
      if(-not $manifestPaths.ContainsKey($relative.ToLowerInvariant())){
        throw "Archive contains unmanifested payload file: $relative"
      }
    }
    if($actualPayload.Count -ne $manifestFiles.Count){
      throw "Manifest/archive file count mismatch: manifest=$($manifestFiles.Count), archive=$($actualPayload.Count)."
    }

    foreach($file in $manifestFiles){
      $relative = [string]$file.path
      $stagePath = Join-Path $stage ($relative.Replace('/', '\'))
      if(-not (Test-Path -LiteralPath $stagePath -PathType Leaf)){ throw "Manifest payload missing from ZIP: $relative" }
      $actualHash = (Get-FileHash -LiteralPath $stagePath -Algorithm SHA256).Hash.ToLowerInvariant()
      $expectedHash = ([string]$file.sha256).ToLowerInvariant()
      if($actualHash -ne $expectedHash){ throw "Payload SHA-256 mismatch before apply: $relative" }
      if($null -ne $file.bytes -and [int64]$file.bytes -ge 0){
        $actualBytes = (Get-Item -LiteralPath $stagePath).Length
        if($actualBytes -ne [int64]$file.bytes){ throw "Payload byte-size mismatch before apply: $relative" }
      }
    }

    Write-UpdateLog $logPath ("VALIDATED: patchId={0}; files={1}; removals={2}" -f $manifest.patchId,$manifestFiles.Count,$removals.Count)

    $newFiles = @()
    foreach($file in $manifestFiles){
      $relative = [string]$file.path
      $destination = Get-SafeDestinationPath -Relative $relative
      if(Test-Path -LiteralPath $destination -PathType Container){ throw "Cannot overwrite directory with file: $relative" }
      if(Test-Path -LiteralPath $destination -PathType Leaf){
        $backupPath = Join-Path $backup ($relative.Replace('/', '\'))
        Copy-WithParent -Source $destination -Destination $backupPath
      } else {
        $newFiles += $relative
      }
    }
    foreach($relativeObject in $removals){
      $relative = [string]$relativeObject
      $destination = Get-SafeDestinationPath -Relative $relative
      if(Test-Path -LiteralPath $destination -PathType Container){ throw "Directory removals are not supported by root patch v1: $relative" }
      if(Test-Path -LiteralPath $destination -PathType Leaf){
        $backupPath = Join-Path $backup ($relative.Replace('/', '\'))
        Copy-WithParent -Source $destination -Destination $backupPath
      }
    }
    if($newFiles.Count -gt 0){ Set-Content -LiteralPath $newFileLedger -Value $newFiles -Encoding UTF8 }

    $rollbackNeeded = $true
    foreach($file in $manifestFiles){
      $relative = [string]$file.path
      $source = Join-Path $stage ($relative.Replace('/', '\'))
      $destination = Get-SafeDestinationPath -Relative $relative
      Copy-WithParent -Source $source -Destination $destination
    }
    foreach($relativeObject in $removals){
      $relative = [string]$relativeObject
      $destination = Get-SafeDestinationPath -Relative $relative
      if(Test-Path -LiteralPath $destination -PathType Leaf){ Remove-Item -LiteralPath $destination -Force }
    }

    foreach($file in $manifestFiles){
      $relative = [string]$file.path
      $destination = Get-SafeDestinationPath -Relative $relative
      if(-not (Test-Path -LiteralPath $destination -PathType Leaf)){ throw "Post-apply file missing: $relative" }
      $actualHash = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant()
      if($actualHash -ne ([string]$file.sha256).ToLowerInvariant()){
        throw "Post-apply SHA-256 mismatch: $relative"
      }
    }
    foreach($relativeObject in $removals){
      $relative = [string]$relativeObject
      $destination = Get-SafeDestinationPath -Relative $relative
      if(Test-Path -LiteralPath $destination){ throw "Post-apply removal assertion failed: $relative" }
    }

    $rollbackNeeded = $false
    $archived = Move-PatchTransport -ZipPath $Patch.FullName -DestinationRoot $appliedRoot -Stamp $stamp
    $lastApplied = [ordered]@{
      schema = 'havenwild.last_applied_patch.v1'
      project = 'Havenwild'
      patchId = [string]$manifest.patchId
      pass = $manifestPass
      appliedUtc = (Get-Date).ToUniversalTime().ToString('o')
      archivedZip = $archived
      files = $manifestFiles.Count
      removals = $removals.Count
    }
    $lastApplied | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $lastAppliedPath -Encoding UTF8
    Write-UpdateLog $logPath ("APPLIED: {0}" -f $manifest.patchId)
    Write-UpdateLog $logPath ("ARCHIVED: {0}" -f $archived)
    Write-UpdateLog $logPath 'CONTINUE: root audit may now proceed into the normal Full quality gate.'
  } catch {
    $failure = $_.Exception.Message
    Write-UpdateLog $logPath ("FAIL: {0}" -f $failure)
    if($rollbackNeeded){
      Write-UpdateLog $logPath 'ROLLBACK: restoring pre-patch files.'
      if(Test-Path -LiteralPath $newFileLedger -PathType Leaf){
        foreach($relative in Get-Content -LiteralPath $newFileLedger){
          if([string]::IsNullOrWhiteSpace($relative)){ continue }
          $destination = Get-SafeDestinationPath -Relative $relative
          if(Test-Path -LiteralPath $destination -PathType Leaf){ Remove-Item -LiteralPath $destination -Force -ErrorAction SilentlyContinue }
        }
      }
      foreach($backupFile in Get-ChildItem -LiteralPath $backup -File -Recurse -ErrorAction SilentlyContinue){
        if($backupFile.FullName -eq $newFileLedger){ continue }
        $relative = $backupFile.FullName.Substring($backup.Length).TrimStart([char[]]'\/')
        $destination = Get-SafeDestinationPath -Relative $relative
        Copy-WithParent -Source $backupFile.FullName -Destination $destination
      }
      Write-UpdateLog $logPath 'ROLLBACK: complete.'
    }
    try { $null = Move-PatchTransport -ZipPath $Patch.FullName -DestinationRoot $failedRoot -Stamp $stamp } catch { }
    throw "Havenwild patch intake failed for $($Patch.Name): $failure"
  } finally {
    if(Test-Path -LiteralPath $stage){ Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue }
  }
}

$patchPatterns = @(
  'Havenwild_IncrementalPatch_*.zip',
  'Havenwild_Patch_*.zip',
  'Havenwild_Handoff_*.zip',
  'Havenwild__*.patch',
  'Havenwild_Patch_*.patch',
  'HW-*.patch'
)
$patchMap = @{}
foreach($pattern in $patchPatterns){
  foreach($candidate in @(Get-ChildItem -LiteralPath $rootFull -File -Filter $pattern -ErrorAction SilentlyContinue)){
    $patchMap[$candidate.FullName.ToLowerInvariant()] = $candidate
  }
}
$patches = @($patchMap.Values | Sort-Object LastWriteTime,Name)
if($patches.Count -eq 0){
  Write-Host 'Patch discovery: 0 recognized pending root patch/handoff ZIP/.patch transport(s).'
  return
}

Write-Host ("Patch discovery: {0} recognized pending root patch/handoff ZIP/.patch transport(s)." -f $patches.Count)
foreach($patch in $patches){ Invoke-OnePatch -Patch $patch }
Write-Host 'Patch intake: all recognized root patch transports applied successfully.'
