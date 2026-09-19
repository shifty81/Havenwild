[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$Root,
  [ValidateSet('Status','Verify','ScenePlan','DraftPlan','Build','Run')][string]$Action='Status'
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
$gateAction=if($Action -eq 'ScenePlan'){'scene-plan'}elseif($Action -eq 'DraftPlan'){'draft-plan'}else{$Action.ToLowerInvariant()}
& $python.Source $gate $gateAction --root $rootPath
$code=$LASTEXITCODE
if($null -eq $code){ exit 2 }
exit [int]$code
