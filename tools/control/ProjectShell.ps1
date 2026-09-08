[CmdletBinding()]
param([Parameter(Mandatory=$false)][string]$Root)
$ErrorActionPreference='Stop'
if([string]::IsNullOrWhiteSpace($Root)) { $Root=(Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path }
$python=Get-Command python -ErrorAction SilentlyContinue
if($null -eq $python){ $python=Get-Command py -ErrorAction SilentlyContinue }
if($null -eq $python){ throw 'Project shell requires Python, but Python was not found.' }
$runner=Join-Path $PSScriptRoot 'ProjectShell.py'
if(-not (Test-Path -LiteralPath $runner -PathType Leaf)){ throw "Project shell runner is missing: $runner" }
& $python.Source $runner --root $Root --action menu
exit $LASTEXITCODE
