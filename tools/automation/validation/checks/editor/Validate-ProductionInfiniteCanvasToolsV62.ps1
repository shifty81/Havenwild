$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\..')).Path
$Python = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } elseif (Get-Command python3 -ErrorAction SilentlyContinue) { "python3" } else { throw "python or python3 is required" }
& $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-ProductionInfiniteCanvasToolsV62.py")
exit $LASTEXITCODE
