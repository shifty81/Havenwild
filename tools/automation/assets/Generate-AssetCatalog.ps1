param(
    [string]$OutputPath = "WORKSPACE\generated\asset-catalog.json"
)

$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$ResolvedOutputPath = Join-Path $Root $OutputPath
$OutputDir = Split-Path -Parent $ResolvedOutputPath

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$IncludedRoots = @(
    "assets",
    "content",
    "crates",
    "docs\legacy_project_docs\design",
    "docs\legacy_project_docs\engineering",
    "tools/automation",
    "web\editor",
    "README.md",
    "Cargo.toml",
    "tools/build/Build.ps1",
    "tools/build/Build.sh"
)

$ExcludedSegments = @(
    "\target\",
    "\WORKSPACE\temp\",
    "\crates\crates\",
    "\.git\",
    "\node_modules\"
)

function Get-RelativePath {
    param([string]$Path)
    $rootPath = $Root
    if (!$rootPath.EndsWith([System.IO.Path]::DirectorySeparatorChar)) {
        $rootPath += [System.IO.Path]::DirectorySeparatorChar
    }
    $rootUri = [System.Uri]::new($rootPath)
    $pathUri = [System.Uri]::new($Path)
    $relative = [System.Uri]::UnescapeDataString($rootUri.MakeRelativeUri($pathUri).ToString())
    return $relative.Replace("\", "/")
}

function Test-IncludedFile {
    param([System.IO.FileInfo]$File)
    $fullName = $File.FullName
    foreach ($segment in $ExcludedSegments) {
        if ($fullName.Contains($segment)) {
            return $false
        }
    }
    return $true
}

function Get-FileHashText {
    param([System.IO.FileInfo[]]$Files)
    $builder = [System.Text.StringBuilder]::new()
    foreach ($file in $Files) {
        $relative = Get-RelativePath $file.FullName
        $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $file.FullName).Hash.ToLowerInvariant()
        [void]$builder.AppendLine("$relative $hash $($file.Length)")
    }
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($builder.ToString())
    $sha = [System.Security.Cryptography.SHA256]::Create()
    return ([System.BitConverter]::ToString($sha.ComputeHash($bytes))).Replace("-", "").ToLowerInvariant()
}

$files = New-Object System.Collections.Generic.List[System.IO.FileInfo]

foreach ($entry in $IncludedRoots) {
    $path = Join-Path $Root $entry
    if (!(Test-Path $path)) {
        continue
    }

    $item = Get-Item -LiteralPath $path
    if ($item.PSIsContainer) {
        Get-ChildItem -LiteralPath $item.FullName -Recurse -File |
            Where-Object { Test-IncludedFile $_ } |
            ForEach-Object { $files.Add($_) }
    } else {
        if (Test-IncludedFile $item) {
            $files.Add($item)
        }
    }
}

$orderedFiles = $files |
    Sort-Object @{ Expression = { Get-RelativePath $_.FullName } }

$records = @()
foreach ($file in $orderedFiles) {
    $relative = Get-RelativePath $file.FullName
    $extension = $file.Extension.TrimStart(".").ToLowerInvariant()
    $records += [ordered]@{
        name = $file.Name
        path = $relative
        extension = $extension
        length = $file.Length
        sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $file.FullName).Hash.ToLowerInvariant()
        lastWriteTime = $file.LastWriteTimeUtc.ToString("o")
    }
}

$assetFiles = $orderedFiles | Where-Object { (Get-RelativePath $_.FullName).StartsWith("assets/") }
$contentFiles = $orderedFiles | Where-Object { (Get-RelativePath $_.FullName).StartsWith("content/") }
$sourceFiles = $orderedFiles | Where-Object {
    $relative = Get-RelativePath $_.FullName
    $relative.StartsWith("crates/") -or $relative -eq "Cargo.toml"
}

$catalog = [ordered]@{
    appInfo = "Havenwild"
    generatedAt = (Get-Date).ToUniversalTime().ToString("o")
    workspaceRoot = $Root
    hashes = [ordered]@{
        sourceTree = Get-FileHashText $sourceFiles
        generatedAssets = Get-FileHashText $assetFiles
        contentData = Get-FileHashText $contentFiles
        assemblyCSharp = Get-FileHashText $sourceFiles
        resourcesAssets = Get-FileHashText $assetFiles
    }
    files = $records
}

$json = $catalog | ConvertTo-Json -Depth 8
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllText($ResolvedOutputPath, $json, $utf8NoBom)
Write-Host "Wrote asset catalog: $ResolvedOutputPath"
Write-Host "Catalog entries: $($records.Count)"
