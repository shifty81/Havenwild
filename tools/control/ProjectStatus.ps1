param([Parameter(Mandatory=$true)][string]$Root)
$ErrorActionPreference='Continue'
Write-Host "Havenwild root: $Root"
Write-Host "Root files: $((Get-ChildItem -LiteralPath $Root -File).Count)"
Write-Host "Cargo workspace: $(Test-Path (Join-Path $Root 'Cargo.toml'))"
Write-Host "Native editor source: $(Test-Path (Join-Path $Root 'apps\haven_editor_native'))"
Write-Host "Game source: $(Test-Path (Join-Path $Root 'crates\haven_game'))"
Write-Host "Logs: $(Join-Path $Root 'logs')"
if(Get-Command git -ErrorAction SilentlyContinue){ Push-Location $Root; git status --short; Pop-Location }
