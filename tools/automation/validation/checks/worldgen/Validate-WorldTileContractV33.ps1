$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\..')).Path
python "$PSScriptRoot/Validate-WorldTileContractV33.py"
