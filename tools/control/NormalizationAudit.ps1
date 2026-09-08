param([Parameter(Mandatory=$true)][string]$Root)
$ErrorActionPreference='Continue'
$stamp=Get-Date -Format 'yyyyMMdd-HHmmss'
$outDir=Join-Path $Root 'docs\audits\generated'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$out=Join-Path $outDir "normalization-audit-$stamp.md"

$ignorePattern='[\\/](target|\.git|artifacts|logs|WORKSPACE[\\/]generated)[\\/]'
$files=Get-ChildItem -LiteralPath $Root -File -Recurse -Force | Where-Object {$_.FullName -notmatch $ignorePattern}
$rootFiles=Get-ChildItem -LiteralPath $Root -File
$bytecode=$files | Where-Object {$_.Extension -eq '.pyc' -or $_.FullName -match '__pycache__'}
$temp=$files | Where-Object {$_.Extension -in @('.tmp','.log')}

$expectedCurrent=@(
  'README.md','CURRENT_SOURCE_HANDOFF.md','ROADMAP.md','DEVELOPMENT_LAYOUT.md',
  'ROOT_LAYOUT.md','SOURCE_ONLY_BOOTSTRAP.md','SOURCE_PACKAGING.md','VALIDATION_ARCHITECTURE.md'
)
$currentDir=Join-Path $Root 'docs\current'
$currentFiles=@()
if (Test-Path $currentDir) {$currentFiles=Get-ChildItem -LiteralPath $currentDir -File | Select-Object -ExpandProperty Name}
$unexpectedCurrent=@($currentFiles | Where-Object {$_ -notin $expectedCurrent})
$missingCurrent=@($expectedCurrent | Where-Object {$_ -notin $currentFiles})

$retired=@(
  'content\animation','content\packs','web\editor','archive\source\legacy_cpp_shell',
  'tools\automation\archive\foreign_open2d_menu','content\build\validator_registry_v2.json',
  'content\build\generated_output_registry_v1.json'
)
$retiredPresent=@($retired | Where-Object {Test-Path (Join-Path $Root $_)})

$architectureScript=Join-Path $Root 'tools\automation\validation\validate_architecture.py'
$architectureStatus='Not run'
if (Test-Path $architectureScript) {
  $python=(Get-Command python -ErrorAction SilentlyContinue)
  if (-not $python) {$python=(Get-Command py -ErrorAction SilentlyContinue)}
  if ($python) {
    $archOutput=& $python.Source $architectureScript 2>&1
    $architectureStatus=if ($LASTEXITCODE -eq 0) {'PASS'} else {'FAIL'}
  } else {
    $architectureStatus='Python unavailable'
  }
}

$registryPath=Join-Path $Root 'content\build\validator_registry_v3.json'
$sourceCount='unknown'; $buildCount='unknown'
if (Test-Path $registryPath) {
  try {
    $registry=Get-Content -LiteralPath $registryPath -Raw | ConvertFrom-Json
    $sourceCount=@($registry.validators | Where-Object {$_.profiles -contains 'source'}).Count
    $buildCount=@($registry.validators | Where-Object {$_.profiles -contains 'build'}).Count
  } catch {}
}

$uiCalls=0
$nativeApp=Join-Path $Root 'apps\haven_editor_native\src\app'
if (Test-Path $nativeApp) {
  Get-ChildItem $nativeApp -Filter '*.rs' -File -ErrorAction SilentlyContinue | ForEach-Object {
    $uiCalls += ([regex]::Matches((Get-Content $_.FullName -Raw),'draw_rectangle\(')).Count
  }
}

$issues=@()
if ($unexpectedCurrent.Count) {$issues += "Unexpected docs/current files: $($unexpectedCurrent -join ', ')"}
if ($missingCurrent.Count) {$issues += "Missing docs/current files: $($missingCurrent -join ', ')"}
if ($retiredPresent.Count) {$issues += "Retired paths present: $($retiredPresent -join ', ')"}
if ($architectureStatus -eq 'FAIL') {$issues += 'Rust architecture/file-size validation failed'}
if ($sourceCount -ne 10) {$issues += "Source validator count is $sourceCount; expected 10"}
if ($buildCount -ne 2) {$issues += "Build validator count is $buildCount; expected 2"}
if ($bytecode.Count) {$issues += "Python bytecode/cache files found: $($bytecode.Count)"}

$status=if ($issues.Count) {'NEEDS WORK'} else {'PASS'}
$lines=@(
'# Havenwild Generated Project-Wide Normalization Audit','',
"Generated: $((Get-Date).ToString('o'))",'',
"**Status: $status**",'',
'## Current authority checks','',
"- Repository files scanned: $($files.Count)",
"- Root files: $($rootFiles.Count)",
"- docs/current files: $($currentFiles.Count) / expected $($expectedCurrent.Count)",
"- Retired live paths present: $($retiredPresent.Count)",
"- Architecture gate: $architectureStatus",
"- Source validators: $sourceCount / expected 10",
"- Build validators: $buildCount / expected 2",
"- Python bytecode/cache files: $($bytecode.Count)",
"- Loose temporary/log files in source: $($temp.Count)",
"- Native-editor direct rectangle calls (migration metric only): $uiCalls",'',
'## Scope rule','',
'- Normalization must replace or retire parallel ownership; it must not add a second framework beside working code.',
'- Keep the seven project foundations: World, Terrain, Runtime, Assets, Simulation, Authoring, Persistence.',
'- F3 remains a lightweight adapter to shared world/authoring services; it is not a second native editor.','',
'## Findings',''
)
if ($issues.Count) {$lines += ($issues | ForEach-Object {"- $_"})} else {$lines += '- No normalization regressions detected by this audit.'}
$lines += @('', '## Next', '',
'1. Run `9. Validate current source` and resolve the first current-authority failure.',
'2. Run `2. Build development (fast)` after source changes.',
'3. Do not increase Rust file-size exceptions to hide coordinator growth.',
'4. Keep expensive PCG/debug derivation out of draw loops and use retained visible-region caches.')
$lines | Set-Content -LiteralPath $out -Encoding UTF8
Write-Host "Normalization audit: $out"
Write-Host "Status: $status"
Write-Host "Architecture: $architectureStatus"
Write-Host "Source validators: $sourceCount"
Write-Host "Retired paths present: $($retiredPresent.Count)"
if ($issues.Count) {exit 1}
