$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$OutDir = Join-Path $Root "assets\generated"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

Add-Type -AssemblyName System.Drawing

function New-TileSheet {
    param(
        [string]$Path,
        [int]$TileSize = 32
    )

    $tiles = @(
        @{ Name = "grass"; A = [System.Drawing.Color]::FromArgb(69,122,71); B = [System.Drawing.Color]::FromArgb(91,145,79) },
        @{ Name = "tall_grass"; A = [System.Drawing.Color]::FromArgb(77,137,72); B = [System.Drawing.Color]::FromArgb(101,161,92) },
        @{ Name = "sand"; A = [System.Drawing.Color]::FromArgb(214,191,131); B = [System.Drawing.Color]::FromArgb(234,214,166) },
        @{ Name = "wet_sand"; A = [System.Drawing.Color]::FromArgb(174,151,111); B = [System.Drawing.Color]::FromArgb(199,183,146) },
        @{ Name = "pebble_shore"; A = [System.Drawing.Color]::FromArgb(146,144,136); B = [System.Drawing.Color]::FromArgb(176,173,164) },
        @{ Name = "road"; A = [System.Drawing.Color]::FromArgb(119,101,75); B = [System.Drawing.Color]::FromArgb(151,126,87) },
        @{ Name = "stone_path"; A = [System.Drawing.Color]::FromArgb(126,120,107); B = [System.Drawing.Color]::FromArgb(154,148,135) },
        @{ Name = "mountain_path"; A = [System.Drawing.Color]::FromArgb(123,116,98); B = [System.Drawing.Color]::FromArgb(160,149,123) },
        @{ Name = "water"; A = [System.Drawing.Color]::FromArgb(54,113,169); B = [System.Drawing.Color]::FromArgb(95,168,212) },
        @{ Name = "shallow_water"; A = [System.Drawing.Color]::FromArgb(72,145,191); B = [System.Drawing.Color]::FromArgb(127,196,222) },
        @{ Name = "deep_water"; A = [System.Drawing.Color]::FromArgb(31,74,121); B = [System.Drawing.Color]::FromArgb(64,116,163) },
        @{ Name = "dirt"; A = [System.Drawing.Color]::FromArgb(98,70,47); B = [System.Drawing.Color]::FromArgb(128,86,52) },
        @{ Name = "cliff"; A = [System.Drawing.Color]::FromArgb(104,92,76); B = [System.Drawing.Color]::FromArgb(146,136,118) },
        @{ Name = "mountain_rock"; A = [System.Drawing.Color]::FromArgb(96,98,102); B = [System.Drawing.Color]::FromArgb(142,145,150) },
        @{ Name = "bridge"; A = [System.Drawing.Color]::FromArgb(122,76,39); B = [System.Drawing.Color]::FromArgb(176,116,58) }
    )

    $bitmap = New-Object System.Drawing.Bitmap ($TileSize * $tiles.Count), $TileSize
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::NearestNeighbor
    $graphics.Clear([System.Drawing.Color]::Transparent)

    for ($i = 0; $i -lt $tiles.Count; $i++) {
        $tile = $tiles[$i]
        $x0 = $i * $TileSize
        $brush = New-Object System.Drawing.SolidBrush $tile.A
        $graphics.FillRectangle($brush, $x0, 0, $TileSize, $TileSize)
        $brush.Dispose()

        $pen = New-Object System.Drawing.Pen $tile.B, 2
        for ($line = 4; $line -lt $TileSize; $line += 8) {
            $graphics.DrawLine($pen, $x0 + 3, $line, $x0 + $TileSize - 3, $line - 2)
        }
        $pen.Dispose()

        if ($tile.Name -like "*water") {
            $pen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(180, 178, 225, 241)), 2
            $graphics.DrawArc($pen, $x0 + 4, 8, 24, 12, 180, 180)
            $graphics.DrawArc($pen, $x0 + 2, 17, 26, 10, 180, 180)
            $pen.Dispose()
        }
        if ($tile.Name -eq "sand" -or $tile.Name -eq "wet_sand" -or $tile.Name -eq "pebble_shore") {
            $dot = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(130, 255, 250, 230))
            $graphics.FillEllipse($dot, $x0 + 7, 9, 3, 3)
            $graphics.FillEllipse($dot, $x0 + 15, 18, 3, 3)
            $graphics.FillEllipse($dot, $x0 + 22, 12, 3, 3)
            $dot.Dispose()
        }
        if ($tile.Name -eq "cliff" -or $tile.Name -eq "mountain_rock") {
            $pen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(120, 40, 40, 40)), 2
            $graphics.DrawLine($pen, $x0 + 6, 7, $x0 + 14, 16)
            $graphics.DrawLine($pen, $x0 + 18, 10, $x0 + 25, 22)
            $pen.Dispose()
        }
        if ($tile.Name -eq "bridge") {
            $pen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(120, 66, 36)), 2
            $graphics.DrawLine($pen, $x0 + 6, 0, $x0 + 6, $TileSize)
            $graphics.DrawLine($pen, $x0 + 16, 0, $x0 + 16, $TileSize)
            $graphics.DrawLine($pen, $x0 + 26, 0, $x0 + 26, $TileSize)
            $pen.Dispose()
        }
    }

    $bitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
    $graphics.Dispose()
    $bitmap.Dispose()
}

$sheetPath = Join-Path $OutDir "prototype_terrain_tiles.png"
New-TileSheet -Path $sheetPath

$manifest = @"
{
  "id": "prototype_terrain_tiles",
  "kind": "tilesheet",
  "tile_size": 32,
  "columns": 5,
  "tiles": ["grass", "tall_grass", "sand", "wet_sand", "pebble_shore", "road", "stone_path", "mountain_path", "water", "shallow_water", "deep_water", "dirt", "cliff", "mountain_rock", "bridge"],
  "source": "scripts/Generate-PrototypeAssets.ps1",
  "output": "assets/generated/prototype_terrain_tiles.png",
  "license": "project-generated-placeholder",
  "notes": "Temporary placeholder terrain tiles covering coast, water depth, cliff, mountain, and bridge workflows."
}
"@

Set-Content -Path (Join-Path $OutDir "prototype_terrain_tiles.json") -Value $manifest
Write-Host "Generated $sheetPath"
