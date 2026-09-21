[CmdletBinding()]
param([string]$Root = (Join-Path $PSScriptRoot '..\..'))
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0
$baseline = 'd9c01b26ec2440f97fc1f6167ee561bc6d43e86e'
$remote = 'https://github.com/shifty81/Havenwild.git'
$terrainSha = 'bcf551ecdaa6c352b72668e8087ebd9934b896dc1c45b2b5252abef76c932309'
$rootPath = (Resolve-Path -LiteralPath $Root -ErrorAction Stop).Path
$verify = Join-Path $PSScriptRoot 'Verify-FullSource.py'
$terrain = Join-Path $PSScriptRoot 'dependencies\Terrain.zip'
$stage = Join-Path $rootPath 'experiments\haven_bevy_candidate\tools\prepare_source.py'
function Invoke-SafeGit([string[]]$GitArgs) {
    & git -C $rootPath @GitArgs
    if ($LASTEXITCODE -ne 0) { throw ('Git failed with exit {0}: {1}' -f $LASTEXITCODE, ($GitArgs -join ' ')) }
}
if (Test-Path -LiteralPath (Join-Path $rootPath '.git')) {
    throw 'This bootstrap is ONLY for an extracted new folder without .git. Do not run it in the existing Havenwild repository. For an existing clone use its own PCC.'
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'Git is required to establish the actual B48R28C4 ancestry.' }
$python = Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if ($null -eq $python) { throw 'Python is required for source manifest/source-art verification.' }
if (-not (Test-Path -LiteralPath $terrain -PathType Leaf)) { throw 'The original Terrain.zip test dependency is missing.' }
$actualTerrainSha=(Get-FileHash -LiteralPath $terrain -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualTerrainSha -ne $terrainSha) { throw 'Original Terrain.zip hash mismatch; aborting before Git initialization.' }
& $python.Source $verify --root $rootPath
if ($LASTEXITCODE -ne 0) { throw 'Full-source file manifest verification failed; aborting before Git initialization.' }
Write-Host '[TEST-COPY] Source checks passed. Initializing Git without replacing the extracted worktree.' -ForegroundColor Cyan
Invoke-SafeGit -GitArgs @('init','-b','experimental')
Invoke-SafeGit -GitArgs @('remote','add','origin',$remote)
Invoke-SafeGit -GitArgs @('fetch','--no-tags','origin','experimental')
& git -C $rootPath cat-file -e ($baseline + '^{commit}')
if ($LASTEXITCODE -ne 0) { throw 'Pinned B48R28C4 commit is not reachable from the fetched remote. Source remains intact; stop for manual reconciliation.' }
# CRITICAL: --mixed updates HEAD and Git INDEX ONLY. Never checkout or hard-reset
# the R28C16R1 files just extracted into this fresh test directory.
Invoke-SafeGit -GitArgs @('reset','--mixed',$baseline)
$branch = (& git -C $rootPath branch --show-current).Trim()
$head = (& git -C $rootPath rev-parse HEAD).Trim()
if ($branch -ne 'experimental' -or $head -ne $baseline) { throw 'Unexpected Git state after mixed reset. Stop.' }
Write-Host '[TEST-COPY] Experimental ancestry established; C16R2 source is unchanged in the worktree.' -ForegroundColor Green
& $python.Source $stage --terrain-zip $terrain
if ($LASTEXITCODE -ne 0) { throw 'Original ElizaWy test-input staging failed. No gate certification was attempted.' }
Write-Host '[TEST-COPY] Exact original summer sheet and credits staged in the ignored candidate only.' -ForegroundColor Green
Write-Host '[TEST-COPY] NEXT: Launch HavenwildTools.cmd, select 1 (Full Quality Gate). Only after PASS consider 2 (commit/push).'
Write-Host '[TEST-COPY] Run & Play / Bevy preview separately after the gate. Neither this bootstrap nor the ZIP claims GREEN or GPU parity.'
