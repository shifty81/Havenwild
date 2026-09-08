[CmdletBinding()]
param(
  [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path,
  [string]$EditorScreenshot,
  [string]$RuntimeScreenshot
)
$ErrorActionPreference='Stop'
$stamp=Get-Date -Format 'yyyyMMdd-HHmmss'
$out=Join-Path $Root "docs\audits\generated\terrain-evidence-$stamp"
New-Item -ItemType Directory -Force -Path $out | Out-Null

$copied=@()
function Copy-Evidence([string]$Path,[string]$Name){
  if($Path -and (Test-Path $Path)){
    $dest=Join-Path $out $Name
    Copy-Item $Path $dest -Force
    $script:copied += $dest
  }
}
Copy-Evidence $EditorScreenshot 'editor.png'
Copy-Evidence $RuntimeScreenshot 'runtime.png'

$latestBuild = Get-ChildItem (Join-Path $Root 'logs') -File -ErrorAction SilentlyContinue |
  Sort-Object LastWriteTime -Descending | Select-Object -First 1
if($latestBuild){ Copy-Evidence $latestBuild.FullName $latestBuild.Name }

Get-ChildItem (Join-Path $Root 'docs\audits\generated') -File -ErrorAction SilentlyContinue |
  Where-Object Name -match 'terrain-(pipeline-)?certification|terrain-acceptance|terrain-gameplay' |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 8 |
  ForEach-Object { Copy-Evidence $_.FullName $_.Name }

$sceneManifest=Join-Path $Root 'content\worldgen\scenes\terrain_acceptance\terrain_acceptance_scene_manifest_v1.json'
Copy-Evidence $sceneManifest 'terrain_acceptance_scene_manifest_v1.json'

$manifest=[ordered]@{
  schema='havenwild.terrain_certification_evidence.v1'
  generatedAt=(Get-Date).ToString('o')
  editorScreenshotPresent=(Test-Path (Join-Path $out 'editor.png'))
  runtimeScreenshotPresent=(Test-Path (Join-Path $out 'runtime.png'))
  files=@(Get-ChildItem $out -File | ForEach-Object { $_.Name })
}
$manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $out 'evidence_manifest.json') -Encoding UTF8
Compress-Archive -Path (Join-Path $out '*') -DestinationPath "$out.zip" -Force
Write-Host "Terrain certification evidence: $out.zip"
