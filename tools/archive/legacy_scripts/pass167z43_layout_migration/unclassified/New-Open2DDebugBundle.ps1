[CmdletBinding()]
param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$OutputDir = "",
    [int]$CommandTimeoutSeconds = 15,
    [int]$MaxFileMB = 32,
    [int]$MaxBundleInputMB = 256
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$Text) {
    Write-Host ("[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $Text) -ForegroundColor Cyan
}

function Write-Ok([string]$Text) {
    Write-Host ("          OK - " + $Text) -ForegroundColor Green
}

function Write-Warn([string]$Text) {
    Write-Host ("          WARN - " + $Text) -ForegroundColor Yellow
}

function Safe-Relative([string]$Path, [string]$Base) {
    $fullPath = [IO.Path]::GetFullPath($Path)
    $fullBase = [IO.Path]::GetFullPath($Base).TrimEnd('\') + '\'
    if (-not $fullPath.StartsWith($fullBase, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path escapes repository root: $Path"
    }
    return $fullPath.Substring($fullBase.Length)
}

if ([string]::IsNullOrWhiteSpace($OutputDir)) {
    $OutputDir = Join-Path $RepoRoot "artifacts\debug"
}

$RepoRoot = (Resolve-Path $RepoRoot).Path
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$name = "Open2D_R020_DebugBundle_$stamp"
$stage = Join-Path $env:TEMP $name

Write-Host ""
Write-Host "============================================================" -ForegroundColor DarkGray
Write-Host " OPEN2D DEBUG BUNDLE COLLECTOR" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor DarkGray
Write-Host (" Repository : " + $RepoRoot)
Write-Host (" Output     : " + $OutputDir)
Write-Host (" Timeout    : " + $CommandTimeoutSeconds + " sec per external command")
Write-Host (" File cap   : " + $MaxFileMB + " MB per file")
Write-Host (" Bundle cap : " + $MaxBundleInputMB + " MB staged input")
Write-Host ""

if (Test-Path $stage) {
    Remove-Item -Recurse -Force $stage
}
New-Item -ItemType Directory -Force -Path $stage | Out-Null

$script:StagedBytes = 0L
$script:StagedFiles = 0
$script:Skipped = New-Object System.Collections.Generic.List[string]
$maxFileBytes = [int64]$MaxFileMB * 1MB
$maxBundleBytes = [int64]$MaxBundleInputMB * 1MB

function Copy-BoundedFile([string]$Source, [string]$RelativeDestination) {
    if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) {
        return
    }

    $item = Get-Item -LiteralPath $Source
    if ($item.Length -gt $maxFileBytes) {
        $script:Skipped.Add(("FILE_TOO_LARGE {0} ({1:N1} MB)" -f $Source, ($item.Length / 1MB)))
        return
    }

    if (($script:StagedBytes + $item.Length) -gt $maxBundleBytes) {
        $script:Skipped.Add(("BUNDLE_CAP {0}" -f $Source))
        return
    }

    $dest = Join-Path $stage $RelativeDestination
    $parent = Split-Path $dest -Parent
    if (-not [string]::IsNullOrWhiteSpace($parent)) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }

    Copy-Item -LiteralPath $Source -Destination $dest -Force
    $script:StagedBytes += $item.Length
    $script:StagedFiles++
}

function Should-SkipDiagnosticFile([string]$FullPath) {
    $normalized = $FullPath.Replace('/', '\').ToLowerInvariant()

    foreach ($token in @(
        '\target\',
        '\node_modules\',
        '\.git\',
        '\build\',
        '\builds\',
        '\dist\',
        '\.open2d\cortex\transactions\'
    )) {
        if ($normalized.Contains($token)) {
            if ($token -eq '\.open2d\cortex\transactions\' -and $normalized.EndsWith('\transaction.json')) {
                return $false
            }
            return $true
        }
    }

    if ($normalized.Contains('\.open2d\cortex\image_artifacts\generated\')) {
        return $true
    }

    return $false
}

function Copy-BoundedTree([string]$RelativeRoot) {
    $sourceRoot = Join-Path $RepoRoot $RelativeRoot
    if (-not (Test-Path -LiteralPath $sourceRoot)) {
        Write-Warn ("Not present: " + $RelativeRoot)
        return
    }

    $beforeFiles = $script:StagedFiles
    $beforeBytes = $script:StagedBytes

    Get-ChildItem -LiteralPath $sourceRoot -File -Recurse -Force -ErrorAction SilentlyContinue | ForEach-Object {
        if (Should-SkipDiagnosticFile $_.FullName) {
            return
        }

        $relative = Safe-Relative $_.FullName $RepoRoot
        Copy-BoundedFile $_.FullName $relative
    }

    $addedFiles = $script:StagedFiles - $beforeFiles
    $addedBytes = $script:StagedBytes - $beforeBytes
    Write-Ok ("{0}: {1} files / {2:N2} MB" -f $RelativeRoot, $addedFiles, ($addedBytes / 1MB))
}

function Capture-CommandTimed([string]$Exe, [string[]]$Args, [string]$Name) {
    $path = Join-Path $stage $Name
    Write-Step ("Capturing " + $Exe + " " + ($Args -join " "))

    try {
        $command = Get-Command $Exe -ErrorAction Stop
        $argsJson = ConvertTo-Json -Compress -InputObject @($Args)

        $job = Start-Job -ScriptBlock {
            param($exePath, $jsonArgs)
            $invokeArgs = @()
            if (-not [string]::IsNullOrWhiteSpace($jsonArgs)) {
                $decoded = ConvertFrom-Json $jsonArgs
                if ($decoded -is [Array]) {
                    $invokeArgs = @($decoded)
                } else {
                    $invokeArgs = @($decoded)
                }
            }
            & $exePath @invokeArgs 2>&1 | Out-String
        } -ArgumentList $command.Source, $argsJson

        $completed = Wait-Job -Job $job -Timeout $CommandTimeoutSeconds
        if ($null -eq $completed) {
            Stop-Job -Job $job -ErrorAction SilentlyContinue
            ("TIMEOUT after {0} seconds: {1} {2}" -f $CommandTimeoutSeconds, $Exe, ($Args -join " ")) |
                Set-Content -LiteralPath $path -Encoding UTF8
            Write-Warn ("Timed out after " + $CommandTimeoutSeconds + " sec; continuing.")
        } else {
            $output = Receive-Job -Job $job -ErrorAction SilentlyContinue | Out-String
            $output | Set-Content -LiteralPath $path -Encoding UTF8
            Write-Ok $Name
        }

        Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
    }
    catch {
        ("UNAVAILABLE: " + $_.Exception.Message) | Set-Content -LiteralPath $path -Encoding UTF8
        Write-Warn ($Exe + ": " + $_.Exception.Message)
    }
}

try {
    Write-Step "Creating staging directory"
    Write-Ok $stage

    Capture-CommandTimed "cargo" @("--version") "cargo-version.txt"
    Capture-CommandTimed "rustc" @("--version") "rustc-version.txt"
    Capture-CommandTimed "rustup" @("show") "rustup-show.txt"
    Capture-CommandTimed "node" @("--version") "node-version.txt"
    Capture-CommandTimed "npm" @("--version") "npm-version.txt"
    Capture-CommandTimed "code" @("--version") "vscode-version.txt"

    Push-Location $RepoRoot
    try {
        Capture-CommandTimed "git" @("status", "--short") "git-status.txt"
    }
    finally {
        Pop-Location
    }

    Write-Step "Collecting key project files"
    $copyFiles = @(
        "Cargo.toml",
        "Cargo.lock",
        "SOURCE_MANIFEST.json",
        "AI_CHECKPOINT_MANIFEST.json",
        "README.md",
        "README_AI_FIRST.md",
        "Open2DTools.cmd",
        "config\architecture\foundry_dependency_policy.json",
        "docs\roadmap\O2D_R007_R020_AI_FOUNDATION_RUN.md",
        "docs\ai\BUILD_DEBUG_CHECKPOINT_R020.md"
    )
    foreach ($relative in $copyFiles) {
        $source = Join-Path $RepoRoot $relative
        if (Test-Path -LiteralPath $source -PathType Leaf) {
            Copy-BoundedFile $source $relative
        }
    }
    Write-Ok ("Key files staged. Total now: {0} files / {1:N2} MB" -f $script:StagedFiles, ($script:StagedBytes / 1MB))

    Write-Step "Collecting Open2D diagnostic state"
    Copy-BoundedTree ".open2d\sessions"
    Copy-BoundedTree ".open2d\cortex"
    Copy-BoundedTree "logs"

    if ($script:Skipped.Count -gt 0) {
        $script:Skipped | Set-Content -LiteralPath (Join-Path $stage "SKIPPED_FILES.txt") -Encoding UTF8
        Write-Warn ("Skipped " + $script:Skipped.Count + " oversized/generated files; see SKIPPED_FILES.txt")
    }

    $summary = [ordered]@{
        schema_version = 2
        generated_at = (Get-Date).ToString("o")
        repository = $RepoRoot
        staged_files = $script:StagedFiles
        staged_bytes = $script:StagedBytes
        staged_megabytes = [Math]::Round(($script:StagedBytes / 1MB), 2)
        skipped_files = $script:Skipped.Count
        per_command_timeout_seconds = $CommandTimeoutSeconds
        max_file_mb = $MaxFileMB
        max_bundle_input_mb = $MaxBundleInputMB
    }
    $summary | ConvertTo-Json -Depth 5 |
        Set-Content -LiteralPath (Join-Path $stage "DEBUG_BUNDLE_SUMMARY.json") -Encoding UTF8

    $zip = Join-Path $OutputDir ($name + ".zip")
    if (Test-Path $zip) {
        Remove-Item -Force $zip
    }

    Write-Step ("Compressing {0} staged files / {1:N2} MB" -f $script:StagedFiles, ($script:StagedBytes / 1MB))
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::CreateFromDirectory(
        $stage,
        $zip,
        [System.IO.Compression.CompressionLevel]::Fastest,
        $false
    )
    Write-Ok ("ZIP created: " + $zip)

    Write-Step "Calculating SHA-256"
    $hash = (Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash.ToLowerInvariant()
    ($hash + "  " + [IO.Path]::GetFileName($zip)) |
        Set-Content -LiteralPath ($zip + ".sha256") -Encoding ASCII
    Write-Ok $hash

    Write-Step "Cleaning staging directory"
    Remove-Item -Recurse -Force $stage -ErrorAction SilentlyContinue
    Write-Ok "Temporary files removed"

    Write-Host ""
    Write-Host "Open2D debug bundle created successfully:" -ForegroundColor Green
    Write-Host ("  " + $zip)
    Write-Host ("SHA-256: " + $hash)
    Write-Host ""
    exit 0
}
catch {
    Write-Host ""
    Write-Host ("DEBUG BUNDLE FAILED: " + $_.Exception.Message) -ForegroundColor Red
    Write-Host ("Staging directory retained for inspection: " + $stage) -ForegroundColor Yellow
    exit 1
}
