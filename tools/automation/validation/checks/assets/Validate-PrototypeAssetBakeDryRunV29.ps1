$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\..')).Path
python "$root/tools/automation/validation/checks/assets/Validate-PrototypeAssetBakeDryRunV29.py"
