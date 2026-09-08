$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\..')).Path
python (Join-Path $PSScriptRoot "Validate-WorldPaintBrushBackendV34.py")
