param([Parameter(Mandatory=$true)][string]$Root)
$ErrorActionPreference='Continue'
$stamp=Get-Date -Format 'yyyyMMdd-HHmmss'
$outDir=Join-Path $Root 'docs\audits\generated'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$out=Join-Path $outDir "normalization-audit-$stamp.md"

$ignorePattern='[\\/](target|\.git|artifacts|logs|WORKSPACE[\\/]generated)[\\/]'
$files=Get-ChildItem -LiteralPath $Root -File -Recurse -Force | Where-Object {$_.FullName -notmatch $ignorePattern}
$bytecode=$files | Where-Object {$_.Extension -eq '.pyc' -or $_.FullName -match '__pycache__'}
$python=(Get-Command python -ErrorAction SilentlyContinue)
if (-not $python) {$python=(Get-Command py -ErrorAction SilentlyContinue)}
$runner=Join-Path $Root 'tools\automation\validation\validation_runner.py'
$sourceCount='unknown'; $buildCount='unknown'; $frameworkCount='unknown'; $listStatus='Not run'
if ($python -and (Test-Path $runner)) {
  $sourceLines=@(& $python.Source $runner source --list 2>&1); $sourceExit=$LASTEXITCODE
  $buildLines=@(& $python.Source $runner build --list 2>&1); $buildExit=$LASTEXITCODE
  $frameworkLines=@(& $python.Source $runner framework --list 2>&1); $frameworkExit=$LASTEXITCODE
  if ($sourceExit -eq 0 -and $buildExit -eq 0 -and $frameworkExit -eq 0) {
    $sourceCount=@($sourceLines | Where-Object {$_ -match '^\d{5}\s'}).Count
    $buildCount=@($buildLines | Where-Object {$_ -match '^\d{5}\s'}).Count
    $frameworkCount=@($frameworkLines | Where-Object {$_ -match '^\d{5}\s'}).Count
    $listStatus='PASS'
  } else {$listStatus='FAIL'}
}
$buildFront=Join-Path $Root 'tools\build\Build.cmd'
$frontDoor='FAIL'
if(Test-Path -LiteralPath $buildFront -PathType Leaf){
  $frontText=Get-Content -LiteralPath $buildFront -Raw
  if($frontText -match 'check_current\.py' -and $frontText -match '--cargo-test' -and $frontText -match ':current_test' -and $frontText -match ':current_validate' -and $frontText -match ':current_certify' -and $frontText -match ':current_framework' -and $frontText -match 'framework-audit'){ $frontDoor='PASS' }
}
$issues=@()
if ($listStatus -ne 'PASS') {$issues += 'Validation v4 registry/profile resolution failed'}
if ($frontDoor -ne 'PASS') {$issues += 'Root Build.cmd does not route generic test/validate/certify/framework-audit through current v4 authority'}
if ($sourceCount -ne 10) {$issues += "Source validator count is $sourceCount; expected 10"}
if ($buildCount -ne 2) {$issues += "Build validator count is $buildCount; expected 2"}
if ($frameworkCount -ne 4) {$issues += "Framework validator count is $frameworkCount; expected 4"}
if ($bytecode.Count) {$issues += "Python bytecode/cache files found: $($bytecode.Count)"}
$status=if ($issues.Count) {'NEEDS WORK'} else {'PASS'}
$lines=@('# Havenwild Generated Project-Wide Normalization Audit','',"Generated: $((Get-Date).ToString('o'))",'',"**Status: $status**",'', '## Validation authority','',
"- Registry/profile resolution: $listStatus", "- Source validators: $sourceCount / expected 10", "- Build validators: $buildCount / expected 2", "- Framework validators: $frameworkCount / expected 4", "- Root build front door: $frontDoor", "- Python bytecode/cache files: $($bytecode.Count)", '', '## Findings','')
if ($issues.Count) {$lines += ($issues | ForEach-Object {"- $_"})} else {$lines += '- No validation-authority normalization regressions detected.'}
$lines += @('', '## Policy','', '- v4 is current authority; v3 remains historical/full-certification compatibility evidence.', '- Pass-specific validators must not accumulate in build/source/framework profiles.', '- Historical validator/evidence files remain preserved unless a separately approved archival cleanup removes them.')
$lines | Set-Content -LiteralPath $out -Encoding UTF8
Write-Host "Normalization audit: $out"; Write-Host "Status: $status"; Write-Host "Source validators: $sourceCount"; Write-Host "Framework validators: $frameworkCount"
if ($issues.Count) {exit 1}
