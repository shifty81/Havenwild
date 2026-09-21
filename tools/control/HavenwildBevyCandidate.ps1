[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$Root,
  [ValidateSet('Status','Verify','ScenePlan','DraftPlan','Build','Run','RunDx12','RunPrimaryProbe','RunDx12PrimaryProbe','InfraAudit','InfraSource','InfraOpen','InfraMapper','InfraPackets','InfraSave','InfraReopen','InfraPie','InfraParity')][string]$Action='Status'
)
$ErrorActionPreference='Stop'
$rootPath=(Resolve-Path -LiteralPath $Root -ErrorAction Stop).Path
$gate=Join-Path $rootPath 'experiments\haven_bevy_candidate\tools\candidate_gate.py'
if(-not (Test-Path -LiteralPath $gate -PathType Leaf)){
  Write-Host 'BLOCKED: Candidate operations are missing.' -ForegroundColor Red
  exit 2
}
$python=Get-Command python -ErrorAction SilentlyContinue
if($null -eq $python){ $python=Get-Command py -ErrorAction SilentlyContinue }
if($null -eq $python){ Write-Host 'BLOCKED: Python unavailable.' -ForegroundColor Red; exit 2 }
# The candidate infrastructure shares this existing PCC-owned dispatcher/job/log path.
# No separate launcher or authorization surface is introduced.
$infra=@{
  InfraAudit='audit'; InfraSource='source'; InfraOpen='open';
  InfraMapper='mapper-queue'; InfraPackets='render-packets';
  InfraSave='save'; InfraReopen='reopen'; InfraPie='pie-plan'; InfraParity='parity'
}
if($infra.ContainsKey($Action)){
  $spine=Join-Path $rootPath 'experiments\haven_bevy_candidate\tools\experiment_spine.py'
  if(-not (Test-Path -LiteralPath $spine -PathType Leaf)){
    Write-Host 'BLOCKED: Candidate infrastructure missing.' -ForegroundColor Red
    exit 2
  }
  & $python.Source $spine $infra[$Action] --root $rootPath
  $infraExit=$LASTEXITCODE
  if($null -eq $infraExit){ exit 2 }
  exit [int]$infraExit
}
$gateAction=if($Action -eq 'ScenePlan'){'scene-plan'}elseif($Action -eq 'DraftPlan'){'draft-plan'}elseif($Action -in @('RunDx12','RunPrimaryProbe','RunDx12PrimaryProbe')){'run'}else{$Action.ToLowerInvariant()}
# Diagnostic subprocess only: each registered mode is explicit and reproducible.
# The caller's environment is not changed by this child PowerShell process.
if($Action -in @('RunDx12','RunDx12PrimaryProbe')) {
  $env:WGPU_BACKEND='dx12'
} elseif($Action -in @('Run','RunPrimaryProbe')) {
  Remove-Item Env:WGPU_BACKEND -ErrorAction SilentlyContinue
}
if($Action -in @('RunPrimaryProbe','RunDx12PrimaryProbe')) {
  $env:HAVENWILD_BEVY_PRIMARY_ONLY='1'
} elseif($Action -in @('Run','RunDx12')) {
  Remove-Item Env:HAVENWILD_BEVY_PRIMARY_ONLY -ErrorAction SilentlyContinue
}
& $python.Source $gate $gateAction --root $rootPath
$code=$LASTEXITCODE
if($null -eq $code){ exit 2 }
exit [int]$code
