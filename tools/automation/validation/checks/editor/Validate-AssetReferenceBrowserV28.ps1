$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\..')).Path
python "$PSScriptRoot/Validate-AssetReferenceBrowserV28.py"
