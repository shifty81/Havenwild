Set-StrictMode -Version 2.0

function Get-PccJobsRoot {
  param([Parameter(Mandatory=$true)][string]$Root)
  $path=Join-Path $Root '.havenwild\jobs'
  New-Item -ItemType Directory -Force -Path $path | Out-Null
  return $path
}

function Write-PccJobReceipt {
  param([string]$Root,[hashtable]$Payload)
  $jobs=Get-PccJobsRoot -Root $Root
  $stamp=Get-Date -Format 'yyyyMMdd-HHmmssfff'
  $path=Join-Path $jobs ("job-$stamp.json")
  $Payload['schema']='havenwild.pcc_job_receipt.v1'
  $Payload | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $path -Encoding UTF8
  Set-Content -LiteralPath (Join-Path $jobs 'LATEST.txt') -Value $path -Encoding UTF8
  return $path
}

function Invoke-PccJob {
  param(
    [Parameter(Mandatory=$true)][string]$Root,
    [Parameter(Mandatory=$true)][string]$Name,
    [Parameter(Mandatory=$true)][scriptblock]$Action,
    [string]$CommandKey=''
  )
  $started=Get-Date
  $result='PASS'; $exitCode=0; $failure=$null
  Write-Host ""
  Write-Host ("START {0}" -f $Name) -ForegroundColor Cyan
  try {
    $global:LASTEXITCODE=0
    & $Action
    if($LASTEXITCODE -ne 0){ throw "Command exited with code $LASTEXITCODE" }
    Write-Host ("PASS {0}" -f $Name) -ForegroundColor Green
  } catch {
    $result='FAIL'; $exitCode=1; $failure=$_.Exception.Message
    Write-Host ("FAIL {0}: {1}" -f $Name,$failure) -ForegroundColor Red
  }
  $ended=Get-Date
  $duration=($ended-$started).TotalSeconds
  $payload=@{
    name=$Name; commandKey=$CommandKey; result=$result; exitCode=$exitCode
    startedUtc=$started.ToUniversalTime().ToString('o')
    endedUtc=$ended.ToUniversalTime().ToString('o')
    durationSeconds=[Math]::Round($duration,3)
    failure=$failure
  }
  $receipt=Write-PccJobReceipt -Root $Root -Payload $payload
  Write-Host ("Job receipt: {0}" -f $receipt) -ForegroundColor DarkGray
  return $exitCode
}

function Get-PccLatestJob {
  param([Parameter(Mandatory=$true)][string]$Root)
  $latest=Join-Path (Get-PccJobsRoot -Root $Root) 'LATEST.txt'
  if(-not (Test-Path -LiteralPath $latest -PathType Leaf)){ return $null }
  $path=(Get-Content -LiteralPath $latest -Raw).Trim()
  if([string]::IsNullOrWhiteSpace($path) -or -not (Test-Path -LiteralPath $path -PathType Leaf)){ return $null }
  try { return Get-Content -LiteralPath $path -Raw | ConvertFrom-Json } catch { return $null }
}
