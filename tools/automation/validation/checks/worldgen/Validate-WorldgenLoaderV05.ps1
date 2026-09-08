$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\..')).Path
$Pack = Join-Path $Root "content\packs\worldgen_home_island_v0_4.json"
$Loader = Join-Path $Root "crates	avern_core\src\worldgen_loader.rs"
$Game = Join-Path $Root "crates	avern_game\src\main.rs"

if (!(Test-Path $Pack)) { throw "Missing worldgen pack: $Pack" }
if (!(Test-Path $Loader)) { throw "Missing loader source: $Loader" }
if (!(Test-Path $Game)) { throw "Missing game source: $Game" }

$packJson = Get-Content $Pack -Raw | ConvertFrom-Json
if (!$packJson.sceneFiles -or $packJson.sceneFiles.Count -lt 1) { throw "Pack has no sceneFiles." }

foreach ($scene in $packJson.sceneFiles) {
    $scenePath = Join-Path $Root $scene
    if (!(Test-Path $scenePath)) { throw "Missing scene file: $scene" }
    $sceneJson = Get-Content $scenePath -Raw | ConvertFrom-Json
    $sceneWidth = [int]$sceneJson.sceneSize[0]
    $sceneHeight = [int]$sceneJson.sceneSize[1]
    $isLegacyScene = ($sceneWidth -eq 48 -and $sceneHeight -eq 32)
    $isExpandedScene = ($sceneWidth -eq 96 -and $sceneHeight -eq 64)
    if (-not ($isLegacyScene -or $isExpandedScene)) { throw "Bad scene size in $scene: ${sceneWidth}x${sceneHeight}" }
    if ($sceneJson.layers.terrain.Count -ne $sceneHeight) { throw "Bad terrain row count in $scene" }
    foreach ($row in $sceneJson.layers.terrain) {
        if ($row.Count -ne $sceneWidth) { throw "Bad terrain width in $scene" }
    }
}

$loaderText = Get-Content $Loader -Raw
if ($loaderText -notmatch "load_worldgen_pack_from_path") { throw "Loader missing load_worldgen_pack_from_path." }
if ($loaderText -notmatch "parse_scene") { throw "Loader missing parse_scene." }

$gameText = Get-Content $Game -Raw
if ($gameText -notmatch "WORLDGEN_PACK_PATH") { throw "Game missing WORLDGEN_PACK_PATH." }
if ($gameText -notmatch "KeyCode::F10") { throw "Game missing F10 reload hook." }

Write-Host "Worldgen loader v0.5 validation: PASS"
Write-Host "Scene files checked:" $packJson.sceneFiles.Count
