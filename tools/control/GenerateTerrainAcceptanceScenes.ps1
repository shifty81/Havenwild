[CmdletBinding()]
param([string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path)

$ErrorActionPreference = 'Stop'
$logDir = Join-Path $Root 'logs\terrain'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$logPath = Join-Path $logDir "terrain-acceptance-generation-$stamp.log"

function Write-GenerationLog {
    param([string]$Message)
    $line = "[{0}] {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Message
    Write-Host $line
    Add-Content -Path $logPath -Value $line
}

Write-GenerationLog "Terrain acceptance generation started"
Write-GenerationLog "Repository root: $Root"
Write-GenerationLog "Log: $logPath"

try {
    $python = Get-Command python -ErrorAction SilentlyContinue
    $usePyLauncher = $false
    if($null -eq $python){
        $python = Get-Command py -ErrorAction SilentlyContinue
        $usePyLauncher = $null -ne $python
    }
    if($null -eq $python){
        throw 'Python 3 was not found on PATH. Install Python 3 or add python/py to PATH.'
    }

    $script = Join-Path $Root 'tools/automation/terrain\Generate-TerrainAcceptanceScenes.py'
    if(-not (Test-Path $script)){
        throw "Missing generator script: $script"
    }

    Write-GenerationLog "Python command: $($python.Source)"
    Write-GenerationLog "Generator script: $script"

    $output = if($usePyLauncher -or $python.Name -ieq 'py.exe'){
        & $python.Source -3 $script --root $Root 2>&1
    } else {
        & $python.Source $script --root $Root 2>&1
    }
    $exitCode = $LASTEXITCODE
    foreach($line in @($output)){
        Write-GenerationLog ([string]$line)
    }
    if($null -eq $exitCode){ $exitCode = 0 }
    if($exitCode -ne 0){
        throw "Generator exited with code $exitCode"
    }

    $manifest = Join-Path $Root 'content\worldgen\scenes\terrain_acceptance\terrain_acceptance_manifest_v1.json'
    if(-not (Test-Path $manifest)){
        throw "Generator completed without producing manifest: $manifest"
    }
    $sceneCount = @((Get-Content $manifest -Raw | ConvertFrom-Json).scenes).Count
    Write-GenerationLog "Generated scene manifest with $sceneCount scene entries"
    Write-GenerationLog 'Terrain acceptance generation completed successfully'
    exit 0
}
catch {
    Write-GenerationLog ("FAIL: {0}" -f $_.Exception.Message)
    Write-Host "Terrain acceptance generation log: $logPath" -ForegroundColor Yellow
    exit 1
}
