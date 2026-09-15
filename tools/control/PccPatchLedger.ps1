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
  foreach($candidate in @(
    @{ Status='FAILED'; Root=(Join-Path $Root 'artifacts\updates\failed') },
    @{ Status='APPLIED'; Root=(Join-Path $Root 'artifacts\updates\applied') }
  )){
    if(-not (Test-Path -LiteralPath $candidate.Root -PathType Container)){ continue }
    $match=Get-ChildItem -LiteralPath $candidate.Root -File -Recurse -Filter $Transport -ErrorAction SilentlyContinue |
      Where-Object { $_.LastWriteTimeUtc -ge $SinceUtc.AddSeconds(-2) } |
      Sort-Object LastWriteTimeUtc -Descending |
      Select-Object -First 1
    if($null -ne $match){
      return [pscustomobject]@{ Status=[string]$candidate.Status; Path=$match.FullName; ModifiedUtc=$match.LastWriteTimeUtc }
    }
  }
  return $null
}
