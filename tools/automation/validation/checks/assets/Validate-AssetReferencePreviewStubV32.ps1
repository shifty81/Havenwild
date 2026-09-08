$ErrorActionPreference = "Stop"
$script = Join-Path $PSScriptRoot "Validate-AssetReferencePreviewStubV32.py"
python $script
