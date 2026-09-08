param([Parameter(Mandatory=$true)][string]$Root,[ValidateSet('clean','repair')][string]$Action)
$ErrorActionPreference='Stop'
if($Action -eq 'clean'){
 foreach($p in @('target','Build')){ $full=Join-Path $Root $p; if(Test-Path $full){ Remove-Item -Recurse -Force $full; Write-Host "Removed $p" } }
}else{
 $removed=0
 Get-ChildItem -Path $Root -Recurse -Directory -Force -ErrorAction SilentlyContinue | Where-Object { $_.Name -in @('__pycache__','.pytest_cache') } | ForEach-Object { Remove-Item -Recurse -Force $_.FullName; $removed++ }
 Write-Host "Removed transient cache directories: $removed"
 & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'AuditRoot.ps1') -Root $Root
}
