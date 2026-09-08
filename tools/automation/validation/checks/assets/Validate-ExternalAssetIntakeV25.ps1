param(
  [string]$Python = "python"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Validator = Join-Path $ScriptDir "Validate-ExternalAssetIntakeV25.py"
& $Python $Validator
exit $LASTEXITCODE
