$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
python "$root/tools/automation/assets/DryRun-PrototypeAssetBakeV29.py"
