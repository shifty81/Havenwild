[CmdletBinding()]
param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path,
    [switch]$SkipBuild
)

$ErrorActionPreference = 'Stop'
$outDir = Join-Path $Root 'docs\audits\generated'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$reportPath = Join-Path $outDir "terrain-pipeline-certification-$timestamp.json"
$markdownPath = Join-Path $outDir "terrain-pipeline-certification-$timestamp.md"

$results = [System.Collections.Generic.List[object]]::new()

function Add-Result {
    param(
        [string]$Name,
        [string]$Status,
        [string]$Detail,
        [int]$ExitCode = 0
    )
    $results.Add([pscustomobject]@{
        name = $Name
        status = $Status
        detail = $Detail
        exitCode = $ExitCode
    })
}

function Invoke-CertificationStep {
    param(
        [string]$Name,
        [scriptblock]$Action
    )
    try {
        & $Action
        $code = if($null -eq $LASTEXITCODE){ 0 } else { $LASTEXITCODE }
        if($code -eq 0){
            Add-Result $Name 'PASS' 'Completed successfully.' 0
        } else {
            Add-Result $Name 'FAIL' "Exited with code $code." $code
        }
    } catch {
        Add-Result $Name 'FAIL' $_.Exception.Message 1
    }
}

Push-Location $Root
try {
    $cargo = Get-Command cargo -ErrorAction SilentlyContinue
    if($null -eq $cargo){
        Add-Result 'cargo availability' 'SKIPPED' 'cargo was not found on PATH.'
        Add-Result 'cargo fmt --check' 'SKIPPED' 'cargo was not found on PATH.'
        Add-Result 'cargo check --workspace' 'SKIPPED' 'cargo was not found on PATH.'
        Add-Result 'haven_core tests' 'SKIPPED' 'cargo was not found on PATH.'
        Add-Result 'haven_world tests' 'SKIPPED' 'cargo was not found on PATH.'
        Add-Result 'native editor check' 'SKIPPED' 'cargo was not found on PATH.'
    } else {
        Add-Result 'cargo availability' 'PASS' (& cargo --version | Out-String).Trim()
        Invoke-CertificationStep 'cargo fmt --check' { cargo fmt --all -- --check }
        Invoke-CertificationStep 'cargo check --workspace' { cargo check --workspace }
        Invoke-CertificationStep 'haven_core tests' { cargo test -p haven_core }
        Invoke-CertificationStep 'haven_world tests' { cargo test -p haven_world }
        Invoke-CertificationStep 'native editor check' { cargo check -p haven_editor_native }
    }

    $sceneGenerator = Join-Path $PSScriptRoot 'GenerateTerrainAcceptanceScenes.ps1'
    if(Test-Path $sceneGenerator){
        Invoke-CertificationStep 'generate terrain acceptance scenes' { & $sceneGenerator -Root $Root }
    } else {
        Add-Result 'generate terrain acceptance scenes' 'FAIL' "Missing script: $sceneGenerator" 1
    }

    foreach($scriptName in @(
        'TerrainGameplayAudit.ps1',
        'TerrainAcceptanceAudit.ps1',
        'TerrainCertificationAudit.ps1'
    )){
        $scriptPath = Join-Path $PSScriptRoot $scriptName
        if(Test-Path $scriptPath){
            Invoke-CertificationStep $scriptName { & $scriptPath -Root $Root }
        } else {
            Add-Result $scriptName 'FAIL' "Missing script: $scriptPath" 1
        }
    }

    $requiredArtifacts = @(
        'assets\generated\worldgen_v0_1\terrain\lpc_mapped_terrain_v7_32.png',
        'assets\generated\worldgen_v0_1\terrain\lpc_mapped_terrain_v7_32.json',
        'content\terrain\havenwild_terrain_standard_v1.json',
        'content\terrain\havenwild_terrain_tuple_catalog_v1.json',
        'content\terrain\havenwild_terrain_gameplay_v1.json',
        'content\terrain\havenwild_terrain_acceptance_v1.json',
        'content\worldgen\scenes\terrain_acceptance\terrain_acceptance_scene_manifest_v1.json',
        'content\worldgen\scenes\terrain_acceptance\wrapped_world_seam_scene_v1.json'
    )
    $missingArtifacts = @($requiredArtifacts | Where-Object {
        -not (Test-Path (Join-Path $Root $_))
    })
    if($missingArtifacts.Count -eq 0){
        Add-Result 'terrain artifact inventory' 'PASS' "$($requiredArtifacts.Count) required artifacts present."
    } else {
        Add-Result 'terrain artifact inventory' 'FAIL' ("Missing: " + ($missingArtifacts -join ', ')) 1
    }

    if($SkipBuild){
        Add-Result 'tools/build/Build.cmd all' 'SKIPPED' 'Skipped by command-line option.'
    } else {
        $buildPath = Join-Path $Root 'tools/build/Build.cmd'
        if(Test-Path $buildPath){
            Invoke-CertificationStep 'tools/build/Build.cmd all' { & $buildPath all }
        } else {
            Add-Result 'tools/build/Build.cmd all' 'FAIL' "Missing tools/build/Build.cmd at repository root." 1
        }
    }
}
finally {
    Pop-Location
}

$failed = @($results | Where-Object status -eq 'FAIL')
$passed = @($results | Where-Object status -eq 'PASS')
$skipped = @($results | Where-Object status -eq 'SKIPPED')
$overall = if($failed.Count -gt 0){ 'FAIL' } elseif($skipped.Count -gt 0){ 'PARTIAL' } else { 'PASS' }

$payload = [ordered]@{
    schema = 'havenwild.terrain_pipeline_certification.v1'
    generatedAt = (Get-Date).ToString('o')
    overallStatus = $overall
    passed = $passed.Count
    failed = $failed.Count
    skipped = $skipped.Count
    results = $results
}
$payload | ConvertTo-Json -Depth 8 | Set-Content -Path $reportPath -Encoding UTF8

$lines = @(
    '# Havenwild Terrain Pipeline Certification',
    '',
    "- Overall: **$overall**",
    "- Passed: $($passed.Count)",
    "- Failed: $($failed.Count)",
    "- Skipped: $($skipped.Count)",
    '',
    '## Results',
    ''
)
foreach($result in $results){
    $lines += "- **$($result.status)** - $($result.name): $($result.detail)"
}
$lines += @(
    '',
    '## Interpretation',
    '',
    '- PASS means all available checks completed successfully.',
    '- PARTIAL means no check failed, but required tooling or an explicitly skipped step prevented full certification.',
    '- FAIL means at least one executed check failed.'
)
$lines | Set-Content -Path $markdownPath -Encoding UTF8

Write-Host "Terrain pipeline certification: $overall"
Write-Host "JSON: $reportPath"
Write-Host "Markdown: $markdownPath"

if($failed.Count -gt 0){ exit 1 }
exit 0
