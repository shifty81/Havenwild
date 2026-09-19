Set-StrictMode -Version 2.0

function Get-PccPatchLedgerPath {
  param([Parameter(Mandatory=$true)][string]$Root)
  $runtime=Join-Path $Root '.havenwild\pcc'
  New-Item -ItemType Directory -Force -Path $runtime | Out-Null
  return Join-Path $runtime 'patch-ledger.json'
}

function Read-PccPatchLedger {
  param([Parameter(Mandatory=$true)][string]$Root)
  $path=Get-PccPatchLedgerPath -Root $Root
  if(-not (Test-Path -LiteralPath $path -PathType Leaf)){
    return [pscustomobject]@{ schema='havenwild.pcc_patch_ledger.v1'; updatedUtc=$null; entries=@() }
  }
  try { return Get-Content -LiteralPath $path -Raw | ConvertFrom-Json } catch {
    return [pscustomobject]@{ schema='havenwild.pcc_patch_ledger.v1'; updatedUtc=$null; entries=@() }
  }
}

function Write-PccPatchLedgerEntry {
  param(
    [Parameter(Mandatory=$true)][string]$Root,
    [Parameter(Mandatory=$true)][string]$Transport,
    [Parameter(Mandatory=$true)][ValidateSet('PENDING','APPLIED','FAILED','DEFERRED')][string]$Status,
    [string]$TargetLane='',
    [bool]$Required=$false,
    [string]$Message=''
  )
  $ledger=Read-PccPatchLedger -Root $Root
  $entries=@($ledger.entries | Where-Object { [string]$_.transport -ne $Transport })
  $entries += [pscustomobject]@{
    transport=$Transport; status=$Status; targetLane=$TargetLane; required=$Required
    message=$Message; updatedUtc=(Get-Date).ToUniversalTime().ToString('o')
  }
  $payload=[ordered]@{ schema='havenwild.pcc_patch_ledger.v1'; updatedUtc=(Get-Date).ToUniversalTime().ToString('o'); entries=$entries }
  $payload | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Get-PccPatchLedgerPath -Root $Root) -Encoding UTF8
}

function Get-PccBlockingPatchFailures {
  param([Parameter(Mandatory=$true)][string]$Root)
  $ledger=Read-PccPatchLedger -Root $Root
  return @($ledger.entries | Where-Object { [bool]$_.required -and [string]$_.status -eq 'FAILED' })
}

function Get-PccPatchArchiveEvidence {
  param(
    [Parameter(Mandatory=$true)][string]$Root,
    [Parameter(Mandatory=$true)][string]$Transport,
    [Parameter(Mandatory=$true)][datetime]$SinceUtc
  )
  # Archive evidence may only apply after this exact root transport disappeared.
  if(Test-Path -LiteralPath (Join-Path $Root $Transport) -PathType Leaf){ return $null }
  foreach($candidate in @(
    @{ Status='FAILED'; Root=(Join-Path $Root 'artifacts\updates\failed') },
    @{ Status='APPLIED'; Root=(Join-Path $Root 'artifacts\updates\applied') }
  )){
    if(-not (Test-Path -LiteralPath $candidate.Root -PathType Container)){ continue }
    $match=Get-ChildItem -LiteralPath $candidate.Root -File -Recurse -Filter $Transport -ErrorAction SilentlyContinue |
      Where-Object { $_.Name.Equals($Transport,[StringComparison]::OrdinalIgnoreCase) } |
      Sort-Object LastWriteTimeUtc -Descending
    # A move retains ZIP LastWriteTimeUtc. Never treat an old ZIP timestamp as
    # evidence of failed intake: inspect exact archived name and manifest.
    foreach($file in @($match)){
      try {
        Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction Stop
        $archive=[IO.Compression.ZipFile]::OpenRead($file.FullName)
        try {
          $entries=@($archive.Entries | Where-Object { $_.FullName -ceq 'PATCH_MANIFEST.json' })
          if($entries.Count -ne 1){ continue }
          $reader=New-Object IO.StreamReader($entries[0].Open())
          try { $manifest=$reader.ReadToEnd() | ConvertFrom-Json -ErrorAction Stop }
          finally { $reader.Dispose() }
          if([string]$manifest.schema -ne 'havenwild.root_patch.v1' -or
             [string]::IsNullOrWhiteSpace([string]$manifest.patchId) -or
             @($manifest.files).Count -eq 0){ continue }
          return [pscustomobject]@{ Status=[string]$candidate.Status; Path=$file.FullName; ModifiedUtc=$file.LastWriteTimeUtc }
        } finally { $archive.Dispose() }
      } catch { continue }
    }
  }
  return $null
}
