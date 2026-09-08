$ErrorActionPreference = "Stop"
$Script = Join-Path $PSScriptRoot "Validate-WorldPaintMaterialAdjacencyV42.py"
python $Script
