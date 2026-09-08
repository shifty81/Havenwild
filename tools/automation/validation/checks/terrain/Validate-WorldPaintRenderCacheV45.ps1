$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..")
python (Join-Path $RepoRoot "tools/automation/validation/checks/terrain/Validate-WorldPaintRenderCacheV45.py")
