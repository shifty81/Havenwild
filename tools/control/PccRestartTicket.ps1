Set-StrictMode -Version 2.0

function Get-PccRuntimeRoot {
  param([Parameter(Mandatory=$true)][string]$Root)
  $path=Join-Path $Root '.havenwild\pcc'
  New-Item -ItemType Directory -Force -Path $path | Out-Null
  return $path
}

function New-PccRestartTicket {
  param(
    [Parameter(Mandatory=$true)][string]$Root,
    [Parameter(Mandatory=$true)][string]$Reason,
    [string]$ResumeCommand='menu',
    [switch]$ReturnToMenu
  )
  $runtime=Get-PccRuntimeRoot -Root $Root
  $path=Join-Path $runtime 'restart-ticket.json'
  $token=[guid]::NewGuid().ToString('N')
  $payload=[ordered]@{
    schema='havenwild.pcc_restart_ticket.v1'
    token=$token
    createdUtc=(Get-Date).ToUniversalTime().ToString('o')
    reason=$Reason
    resumeCommand=$ResumeCommand
    returnToMenu=[bool]$ReturnToMenu
    consumed=$false
  }
  $payload | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $path -Encoding UTF8
  return [pscustomobject]@{ Token=$token; Path=$path; ResumeCommand=$ResumeCommand }
}

function Consume-PccRestartTicket {
  param([Parameter(Mandatory=$true)][string]$Root,[string]$Token)
  if([string]::IsNullOrWhiteSpace($Token)){ return $null }
  $path=Join-Path (Get-PccRuntimeRoot -Root $Root) 'restart-ticket.json'
  if(-not (Test-Path -LiteralPath $path -PathType Leaf)){ return $null }
  try { $ticket=Get-Content -LiteralPath $path -Raw | ConvertFrom-Json } catch { return $null }
  if([string]$ticket.schema -ne 'havenwild.pcc_restart_ticket.v1'){ return $null }
  if([string]$ticket.token -ne $Token){ return $null }
  Remove-Item -LiteralPath $path -Force -ErrorAction SilentlyContinue
  $consumed=Join-Path (Get-PccRuntimeRoot -Root $Root) 'last-restart-consumed.json'
  [ordered]@{
    schema='havenwild.pcc_restart_consumed.v1'
    token=$Token
    consumedUtc=(Get-Date).ToUniversalTime().ToString('o')
    reason=[string]$ticket.reason
    resumeCommand=[string]$ticket.resumeCommand
  } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $consumed -Encoding UTF8
  return $ticket
}

function Start-PccReplacement {
  param(
    [Parameter(Mandatory=$true)][string]$Root,
    [Parameter(Mandatory=$true)][string]$Reason,
    [string]$ResumeCommand='menu',
    [string]$Pass='manual',
    [switch]$ReturnToMenu,
    [switch]$WaitForCompletion
  )
  $ticket=New-PccRestartTicket -Root $Root -Reason $Reason -ResumeCommand $ResumeCommand -ReturnToMenu:$ReturnToMenu
  $host=Join-Path $Root 'tools\control\HavenwildPccHost.ps1'
  $args=@('-NoProfile','-ExecutionPolicy','Bypass','-File',("`"{0}`"" -f $host),'-Command',$ResumeCommand,'-Pass',$Pass,'-RestartToken',$ticket.Token)
  if($ReturnToMenu){ $args += '-ReturnToMenu' }
  if($WaitForCompletion){
    $process=Start-Process -FilePath 'powershell.exe' -ArgumentList $args -WorkingDirectory $Root -Wait -PassThru
    return [pscustomobject]@{ Token=$ticket.Token; Path=$ticket.Path; ResumeCommand=$ResumeCommand; ExitCode=[int]$process.ExitCode }
  }
  Start-Process -FilePath 'powershell.exe' -ArgumentList $args -WorkingDirectory $Root | Out-Null
  return [pscustomobject]@{ Token=$ticket.Token; Path=$ticket.Path; ResumeCommand=$ResumeCommand; ExitCode=0 }
}
