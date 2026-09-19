Set-StrictMode -Version 2.0

function Get-PccRootHandoffSidecar {
  param([Parameter(Mandatory=$true)][string]$ArchivePath)
  foreach($candidate in @("$ArchivePath.sha256", "$ArchivePath.sha256.txt")){
    if(Test-Path -LiteralPath $candidate -PathType Leaf){ return $candidate }
  }
  return $null
}

function Test-PccRootHandoffHash {
  param([Parameter(Mandatory=$true)][string]$ArchivePath)
  $sidecar=Get-PccRootHandoffSidecar -ArchivePath $ArchivePath
  if(-not $sidecar){ return [pscustomobject]@{ Valid=$true; Sidecar=$null; Message='No sidecar supplied.' } }
  try {
    $text=(Get-Content -LiteralPath $sidecar -Raw -ErrorAction Stop).Trim()
    if($text -notmatch '(?i)^([a-f0-9]{64})(?:\s+\*?.+)?$'){
      return [pscustomobject]@{ Valid=$false; Sidecar=$sidecar; Message='Malformed SHA-256 sidecar.' }
    }
    $expected=$Matches[1].ToLowerInvariant()
    $actual=(Get-FileHash -LiteralPath $ArchivePath -Algorithm SHA256).Hash.ToLowerInvariant()
    if($actual -ne $expected){
      return [pscustomobject]@{ Valid=$false; Sidecar=$sidecar; Message='SHA-256 mismatch.' }
    }
    return [pscustomobject]@{ Valid=$true; Sidecar=$sidecar; Message='SHA-256 verified.' }
  } catch {
    return [pscustomobject]@{ Valid=$false; Sidecar=$sidecar; Message=$_.Exception.Message }
  }
}

function Move-PccRootHandoffArtifacts {
  [CmdletBinding()]
  param([Parameter(Mandatory=$true)][string]$Root)

  $rootResolved=(Resolve-Path -LiteralPath $Root).Path
  $patterns=@(
    'Havenwild_CumulativeSourceRollup_*.zip',
    'Havenwild_FullSourceRollup_*.zip',
    'Havenwild_SourceRollup_*.zip',
    'Havenwild_SourceSnapshot_*.zip'
  )
  $map=@{}
  foreach($pattern in $patterns){
    foreach($candidate in @(Get-ChildItem -LiteralPath $rootResolved -File -Filter $pattern -ErrorAction SilentlyContinue)){
      $map[$candidate.FullName.ToLowerInvariant()]=$candidate
    }
  }
  $archives=@($map.Values | Sort-Object LastWriteTime,Name)
  if($archives.Count -eq 0){ return 0 }

  $stamp=Get-Date -Format 'yyyyMMdd-HHmmss'
  $receivedRoot=Join-Path $rootResolved ("artifacts\packages\received\{0}" -f $stamp)
  $quarantineRoot=Join-Path $rootResolved ("artifacts\packages\quarantine\{0}" -f $stamp)
  $moved=0

  foreach($archive in $archives){
    $check=Test-PccRootHandoffHash -ArchivePath $archive.FullName
    $destinationRoot=if([bool]$check.Valid){$receivedRoot}else{$quarantineRoot}
    New-Item -ItemType Directory -Force -Path $destinationRoot | Out-Null
    $destination=Join-Path $destinationRoot $archive.Name
    if(Test-Path -LiteralPath $destination){ Remove-Item -LiteralPath $destination -Force }
    Move-Item -LiteralPath $archive.FullName -Destination $destination -Force
    if($null -ne $check.Sidecar -and (Test-Path -LiteralPath $check.Sidecar -PathType Leaf)){
      $sidecarDestination=Join-Path $destinationRoot (Split-Path -Leaf $check.Sidecar)
      if(Test-Path -LiteralPath $sidecarDestination){ Remove-Item -LiteralPath $sidecarDestination -Force }
      Move-Item -LiteralPath $check.Sidecar -Destination $sidecarDestination -Force
    }
    if([bool]$check.Valid){
      Write-Host ("ROOT HANDOFF: archived non-installable source rollup -> {0} ({1})" -f $destination,$check.Message) -ForegroundColor DarkCyan
    } else {
      Write-Host ("ROOT HANDOFF WARNING: quarantined source rollup -> {0} ({1})" -f $destination,$check.Message) -ForegroundColor Yellow
    }
    $moved++
  }
  return $moved
}


# A browser's " (1)" filename is not a distinct patch identity. Normalize it
# BEFORE the PCC registers pending ledger entries. Never mark held downloads APPLIED.
function Resolve-PccBrowserRenamedDownloads {
  [CmdletBinding()]
  param([Parameter(Mandatory=$true)][string]$Root)
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  $rootFull=(Resolve-Path -LiteralPath $Root).Path
  $moved=0
  foreach($candidate in @(Get-ChildItem -LiteralPath $rootFull -File -Filter 'Havenwild_*Patch_*.zip' -ErrorAction SilentlyContinue)){
    if($candidate.Name -notmatch '^(Havenwild_(?:CUMULATIVE_PCC_Patch|IncrementalPatch|Patch)_.+?) \([0-9]+\)(\.zip)$'){ continue }
    $canonical=$Matches[1]+$Matches[2]
    $sidecar=Get-PccRootHandoffSidecar -ArchivePath $candidate.FullName
    $check=Test-PccRootHandoffHash -ArchivePath $candidate.FullName
    if(-not [bool]$check.Valid){
      Write-Warning ("PATCH HOLD: bad checksum for {0}; leaving in root for investigation: {1}" -f $candidate.Name,$check.Message)
      continue
    }
    $archive=$null
    try {
      $archive=[IO.Compression.ZipFile]::OpenRead($candidate.FullName)
      $entries=@($archive.Entries | Where-Object { $_.FullName -ceq 'PATCH_MANIFEST.json' })
      if($entries.Count -ne 1){ throw 'Expected exactly one root PATCH_MANIFEST.json.' }
      $reader=New-Object IO.StreamReader($entries[0].Open())
      try { $manifest=$reader.ReadToEnd() | ConvertFrom-Json -ErrorAction Stop }
      finally { $reader.Dispose() }
      if([string]$manifest.schema -ne 'havenwild.root_patch.v1' -or
         [string]$manifest.project -ne 'Havenwild' -or
         [string]$manifest.applyMode -ne 'overwrite' -or
         [string]::IsNullOrWhiteSpace([string]$manifest.patchId) -or
         @($manifest.files).Count -lt 1){ throw 'Unrecognized patch identity.' }
    } catch {
      Write-Warning ("PATCH HOLD: invalid browser-renamed ZIP {0}: {1}. Retained for inspection." -f $candidate.Name,$_.Exception.Message)
      continue
    } finally { if($null -ne $archive){ $archive.Dispose() } }
    $canonicalPath=Join-Path $rootFull $canonical
    if(-not (Test-Path -LiteralPath $canonicalPath)){
      # Only a verified, uniquely named candidate can become the normal pending
      # transport. It still requires the user's explicit PCC apply approval.
      Move-Item -LiteralPath $candidate.FullName -Destination $canonicalPath -ErrorAction Stop
      if($sidecar){ $suffix=$sidecar.Substring($candidate.FullName.Length); Move-Item -LiteralPath $sidecar -Destination ($canonicalPath + $suffix) -ErrorAction Stop }
      Write-Host ("PATCH NAME NORMALIZED: {0} -> {1} [PENDING, not applied]" -f $candidate.Name,$canonical) -ForegroundColor Cyan
      $moved++
      continue
    }
    # Multiple candidates are never silently substituted for one another.
    # Preserve differing hashes for review rather than picking the newest.
    $hash=(Get-FileHash -LiteralPath $candidate.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    $canonicalHash=(Get-FileHash -LiteralPath $canonicalPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $holding=Join-Path $rootFull ('artifacts\updates\held-duplicate-downloads\' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Force -Path $holding | Out-Null
    $destination=Join-Path $holding $candidate.Name
    Move-Item -LiteralPath $candidate.FullName -Destination $destination -ErrorAction Stop
    if($sidecar){ Move-Item -LiteralPath $sidecar -Destination (Join-Path $holding (Split-Path -Leaf $sidecar)) -ErrorAction Stop }
    $note=[ordered]@{ schema='havenwild.held_patch.v1'; originalName=$candidate.Name; canonicalName=$canonical; sha256=$hash; canonicalSha256=$canonicalHash; sameBytes=($hash -eq $canonicalHash); status='HELD_NOT_APPLIED'; reason='Browser-renamed duplicate; requires canonical intake only.' }
    $note | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $holding 'holding-receipt.json') -Encoding UTF8
    Write-Host ("PATCH HELD (NOT APPLIED): {0}; same bytes as canonical: {1}; {2}" -f $candidate.Name,($hash -eq $canonicalHash),$destination) -ForegroundColor Yellow
    $moved++
  }
  return $moved
}
