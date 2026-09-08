$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $ScriptDir
python (Join-Path $Root "tools/automation/validation/checks/terrain/Validate-WorldPaintMirrorAndPixelEditorV36.py")
