$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $ScriptDir
python (Join-Path $ScriptDir "Validate-PrototypeAssetImportAdapterV26.py")
