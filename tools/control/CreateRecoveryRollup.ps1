[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$Root)

$ErrorActionPreference = 'Stop'
$tool = Join-Path $Root 'tools\automation\packaging\Create-RecoveryRollup.py'
if (-not (Test-Path -LiteralPath $tool -PathType Leaf)) {
    throw "Recovery rollup tool is missing: $tool"
}

$python = Get-Command py -ErrorAction SilentlyContinue
if ($null -ne $python) {
    & $python.Source -3 $tool --root $Root
    exit $LASTEXITCODE
}

$python = Get-Command python -ErrorAction SilentlyContinue
if ($null -ne $python) {
    & $python.Source $tool --root $Root
    exit $LASTEXITCODE
}

throw 'Python is required to create a recovery rollup, but py/python was not found on PATH.'
