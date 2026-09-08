param(
    [string]$OutputDirectory = "artifacts/authoring-changes"
)
$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$Current = Join-Path $Root 'WORKSPACE/authoring/changesets/current'
if (-not (Test-Path $Current)) {
    Write-Host 'No current authoring changeset exists.'
    exit 0
}
$Manifest = Join-Path $Current 'manifest.json'
if (-not (Test-Path $Manifest)) {
    Write-Host 'No current authoring manifest exists.'
    exit 0
}
$OutRoot = Join-Path $Root $OutputDirectory
New-Item -ItemType Directory -Force -Path $OutRoot | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$Stage = Join-Path $env:TEMP "HavenwildAuthoring-$Stamp"
New-Item -ItemType Directory -Force -Path $Stage | Out-Null
Copy-Item -Recurse -Force $Current (Join-Path $Stage 'changeset')
$data = Get-Content $Manifest -Raw | ConvertFrom-Json
$paths = @()
foreach ($entry in $data.entries) {
    foreach ($relative in $entry.outputPaths) {
        if (-not $relative) { continue }
        $source = Join-Path $Root $relative
        if (-not (Test-Path $source)) { continue }
        $dest = Join-Path $Stage $relative
        $parent = Split-Path $dest -Parent
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
        Copy-Item -Force $source $dest
        $paths += $relative
    }
}
$summary = @(
    '# Havenwild Authoring ChangeSet',
    '',
    "Generated: $(Get-Date -Format o)",
    "Entries: $($data.entries.Count)",
    "Included outputs: $($paths.Count)",
    '',
    'This package contains only explicit hand-authored deltas and their manifest. Generated/source reference layers are not flattened into the package.'
)
Set-Content -Encoding UTF8 (Join-Path $Stage 'AUTHORING_SUMMARY.md') $summary
$Zip = Join-Path $OutRoot "Havenwild_AuthoringChanges_$Stamp.zip"
Compress-Archive -Path (Join-Path $Stage '*') -DestinationPath $Zip -CompressionLevel Optimal
$Hash = (Get-FileHash -Algorithm SHA256 $Zip).Hash.ToLowerInvariant()
Set-Content -Encoding ASCII "$Zip.sha256.txt" "$Hash  $(Split-Path $Zip -Leaf)"
Remove-Item -Recurse -Force $Stage
Write-Host "AUTHORING CHANGESET: $Zip"
Write-Host "SHA-256: $Hash"
