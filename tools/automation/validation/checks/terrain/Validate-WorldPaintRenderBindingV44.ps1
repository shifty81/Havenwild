$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $ScriptDir
python "$Root/tools/automation/validation/checks/terrain/Validate-WorldPaintRenderBindingV44.py"
