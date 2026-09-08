$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Py = Join-Path $ScriptDir "Validate-DonorReferenceAssetCatalogV27.py"
python $Py
