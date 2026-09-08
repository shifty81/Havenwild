[CmdletBinding()]
param([string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path)
$ErrorActionPreference = 'Stop'
$python = Get-Command python -ErrorAction SilentlyContinue
if(-not $python){ $python = Get-Command py -ErrorAction SilentlyContinue }
if(-not $python){ throw 'Python is required to rebuild the terrain atlas.' }
$script = Join-Path $Root 'tools/automation/terrain\Build-LpcMappedTerrainV7.py'
if(-not (Test-Path $script)){ throw "Terrain builder missing: $script" }
Push-Location $Root
try {
  if($python.Name -eq 'py.exe'){ & $python.Source -3 $script }
  else { & $python.Source $script }
  if($LASTEXITCODE -ne 0){ throw "Terrain atlas rebuild failed with exit code $LASTEXITCODE" }
} finally { Pop-Location }
Write-Host 'Terrain runtime atlas rebuilt successfully.' -ForegroundColor Green
