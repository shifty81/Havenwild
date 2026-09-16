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
