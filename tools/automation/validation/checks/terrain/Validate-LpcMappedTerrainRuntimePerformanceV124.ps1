$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
python (Join-Path $ScriptDir "Validate-LpcMappedTerrainRuntimePerformanceV124.py")
