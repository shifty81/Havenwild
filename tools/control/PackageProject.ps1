param(
  [Parameter(Mandatory=$true)][string]$Root,
  [ValidateSet('patch','rollup','baseline','handoff')][string]$Mode,
  [string]$Pass='manual'
)

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path -LiteralPath $Root).Path.TrimEnd([char[]]"\/")

# Packaging and baseline capture are source-authority operations. Refuse to ship or
# bless a repository that violates Havenwild's intentionally boring root contract.
$rootAudit = Join-Path $PSScriptRoot 'AuditRoot.ps1'
if(-not (Test-Path -LiteralPath $rootAudit -PathType Leaf)) {
  throw "Root cleanliness validator is missing: $rootAudit"
}
& $rootAudit -Root $Root
if($LASTEXITCODE -ne 0) {
  throw 'Root cleanliness audit failed. Move package notes/reports under docs/, manifests/, artifacts/, or logs/ before packaging.'
}
$stamp = Get-Date -Format 'yyyyMMdd'
$handoffStamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$outDir = Join-Path $Root 'artifacts\packages'
$baselineDir = Join-Path $Root '.havenwild'
$baselinePath = Join-Path $baselineDir 'package-baseline.json'
New-Item -ItemType Directory -Force -Path $outDir,$baselineDir | Out-Null

# Source packages intentionally exclude machine-local state, build products,
# logs, downloaded imports, and raw third-party dependency mounts. Those
# dependencies are restored through the pinned Havenwild bootstrap flow.
$excludedRootNames = @(
  '.git',
  '.havenwild',
  '.local',
  '.logs',
  'artifacts',
  'Build',
  'IMPORTS',
  'logs',
  'target'
)
$excludedPathPrefixes = @(
  'assets/source/licensed',
  'WORKSPACE/generated',
  'WORKSPACE/dev_bridge',
  'WORKSPACE/test-output',
  'WORKSPACE/saves',
  'WORKSPACE/recovery',
  'WORKSPACE/profiles',
  'node_modules'
)

# Complete Source Rollups use a stricter reproducible-source policy than
# incremental patches/baselines. Patches must still be able to transport a
# newly-authored Havenwild asset, while normal rollups may omit downloaded
# dependencies, generated caches, and historical packaging evidence that the
# bootstrap/tooling can reconstruct.
$sourceRollupPolicyPath = Join-Path $Root 'content\architecture\havenwild_source_rollup_policy_v1.json'
$sourceRollupPolicy = $null
$rollupExcludedPrefixes = @()
$rollupExcludedExactPaths = @()
$rollupExcludedNamePatterns = @()
$rollupAlwaysRetainPrefixes = @()
if(Test-Path -LiteralPath $sourceRollupPolicyPath -PathType Leaf) {
  $sourceRollupPolicy = Get-Content -LiteralPath $sourceRollupPolicyPath -Raw | ConvertFrom-Json
  $rollupExcludedPrefixes = @($sourceRollupPolicy.normalRollup.excludePrefixes)
  $rollupExcludedExactPaths = @($sourceRollupPolicy.normalRollup.excludeExactPaths)
  $rollupExcludedNamePatterns = @($sourceRollupPolicy.normalRollup.excludeNamePatterns)
  $rollupAlwaysRetainPrefixes = @($sourceRollupPolicy.normalRollup.alwaysRetainPrefixes)
} elseif($Mode -eq 'rollup') {
  throw "Lean source-rollup policy is missing: $sourceRollupPolicyPath"
}

function Convert-ToProjectRelativePath {
  param([Parameter(Mandatory=$true)][string]$FullName)

  if(-not $FullName.StartsWith($Root, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Path is outside the Havenwild repository root: $FullName"
  }

  # TrimStart expects individual Char values. The historical '\\' argument was
  # a two-character String and caused complete-source packaging to fail.
  return $FullName.Substring($Root.Length).TrimStart([char[]]"\/").Replace('\','/')
}

function Test-ExcludedProjectPath {
  param(
    [Parameter(Mandatory=$true)][string]$RelativePath,
    [System.IO.FileSystemInfo]$Item
  )

  $normalized = $RelativePath.Replace('\','/').Trim([char[]]"\/")
  if([string]::IsNullOrWhiteSpace($normalized)) { return $false }

  $segments = @($normalized -split '/')
  if($segments.Count -gt 0 -and $excludedRootNames -contains $segments[0]) {
    return $true
  }

  foreach($prefix in $excludedPathPrefixes) {
    if($normalized.Equals($prefix, [System.StringComparison]::OrdinalIgnoreCase) -or
       $normalized.StartsWith($prefix + '/', [System.StringComparison]::OrdinalIgnoreCase)) {
      return $true
    }
  }

  if($segments -contains '__pycache__' -or $segments -contains 'node_modules') {
    return $true
  }
  if($normalized.EndsWith('.pyc', [System.StringComparison]::OrdinalIgnoreCase) -or
     $normalized.EndsWith('.pyo', [System.StringComparison]::OrdinalIgnoreCase)) {
    return $true
  }

  # Never traverse or package machine-local junction/symlink targets.
  if($null -ne $Item -and
     (($Item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)) {
    return $true
  }

  return $false
}

function Get-ProjectFilesFromDirectory {
  param([Parameter(Mandatory=$true)][string]$Directory)

  foreach($item in Get-ChildItem -LiteralPath $Directory -Force) {
    $relative = Convert-ToProjectRelativePath -FullName $item.FullName
    if(Test-ExcludedProjectPath -RelativePath $relative -Item $item) {
      continue
    }

    if($item.PSIsContainer) {
      Get-ProjectFilesFromDirectory -Directory $item.FullName
    } else {
      Write-Output $item
    }
  }
}

function Get-ProjectFiles {
  Get-ProjectFilesFromDirectory -Directory $Root
}

function Test-RollupExcludedProjectPath {
  param([Parameter(Mandatory=$true)][string]$RelativePath)

  $normalized = $RelativePath.Replace('\','/').Trim([char[]]"\/")
  if([string]::IsNullOrWhiteSpace($normalized)) { return $false }

  foreach($prefix in $rollupAlwaysRetainPrefixes) {
    $cleanPrefix = ([string]$prefix).Replace('\','/').Trim([char[]]"\/")
    if($normalized.Equals($cleanPrefix, [System.StringComparison]::OrdinalIgnoreCase) -or
       $normalized.StartsWith($cleanPrefix + '/', [System.StringComparison]::OrdinalIgnoreCase)) {
      return $false
    }
  }

  foreach($exact in $rollupExcludedExactPaths) {
    $cleanExact = ([string]$exact).Replace('\','/').Trim([char[]]"\/")
    if($normalized.Equals($cleanExact, [System.StringComparison]::OrdinalIgnoreCase)) {
      return $true
    }
  }

  foreach($prefix in $rollupExcludedPrefixes) {
    $cleanPrefix = ([string]$prefix).Replace('\','/').Trim([char[]]"\/")
    if($normalized.Equals($cleanPrefix, [System.StringComparison]::OrdinalIgnoreCase) -or
       $normalized.StartsWith($cleanPrefix + '/', [System.StringComparison]::OrdinalIgnoreCase)) {
      return $true
    }
  }

  $name = [System.IO.Path]::GetFileName($normalized)
  foreach($pattern in $rollupExcludedNamePatterns) {
    if($name -like [string]$pattern) { return $true }
  }
  return $false
}

function Get-RollupProjectFiles {
  foreach($file in Get-ProjectFiles) {
    $relative = Convert-ToProjectRelativePath -FullName $file.FullName
    if(-not (Test-RollupExcludedProjectPath -RelativePath $relative)) {
      Write-Output $file
    }
  }
}

function Get-Snapshot {
  $result = [ordered]@{}
  foreach($file in Get-ProjectFiles) {
    $relative = Convert-ToProjectRelativePath -FullName $file.FullName
    $result[$relative] = [ordered]@{
      sha256 = (Get-FileHash $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
      bytes = $file.Length
    }
  }
  return $result
}


function Write-Utf8NoBom {
  param(
    [Parameter(Mandatory=$true)][string]$Path,
    [Parameter(Mandatory=$true)][string]$Text
  )

  $encoding = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Text, $encoding)
}

function Invoke-StagingZip {
  param(
    [Parameter(Mandatory=$true)][string]$SourceDirectory,
    [Parameter(Mandatory=$true)][string]$DestinationZip
  )

  $zipHelper = Join-Path $Root 'tools\automation\packaging\Create-ZipFromDirectory.py'
  if(-not (Test-Path -LiteralPath $zipHelper -PathType Leaf)) {
    throw "Reliable ZIP helper is missing: $zipHelper"
  }
  $python = Get-Command python -ErrorAction SilentlyContinue
  if($null -eq $python) {
    throw 'Python is required for Havenwild packaging but was not found on PATH.'
  }

  & $python.Source $zipHelper --source $SourceDirectory --output $DestinationZip --compression-level 9
  if($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $DestinationZip -PathType Leaf)) {
    throw "ZIP packaging helper failed with exit code $LASTEXITCODE."
  }
}

function Save-Baseline {
  param(
    [Parameter(Mandatory=$true)][object]$Files,
    [Parameter(Mandatory=$true)][string]$BaselinePass
  )

  $payload = [ordered]@{
    version = 3
    capturedUtc = (Get-Date).ToUniversalTime().ToString('o')
    sourcePolicy = 'havenwild_owned_source_only'
    pass = $BaselinePass
    files = $Files
  }
  $json = ($payload | ConvertTo-Json -Depth 8) + [Environment]::NewLine
  Write-Utf8NoBom -Path $baselinePath -Text $json
  Write-Host "Baseline created: $baselinePath"
  Write-Host "Tracked files: $($Files.Count)"
}

function Resolve-EffectivePass {
  if(-not [string]::IsNullOrWhiteSpace($Pass) -and $Pass -ne 'manual') {
    return $Pass
  }

  # Root-drop updates record the most recently accepted pass under machine-local
  # .havenwild state. Prefer that over historical cumulative manifests.
  $lastAppliedPath = Join-Path $Root '.havenwild\updates\last-applied.json'
  if(Test-Path -LiteralPath $lastAppliedPath -PathType Leaf) {
    try {
      $lastApplied = Get-Content -LiteralPath $lastAppliedPath -Raw | ConvertFrom-Json
      if(-not [string]::IsNullOrWhiteSpace([string]$lastApplied.pass)) {
        return [string]$lastApplied.pass
      }
    } catch {
      # Fall through to baseline/historical discovery.
    }
  }

  if(Test-Path -LiteralPath $baselinePath -PathType Leaf) {
    try {
      $baselineMetadata = Get-Content -LiteralPath $baselinePath -Raw | ConvertFrom-Json
      if(-not [string]::IsNullOrWhiteSpace([string]$baselineMetadata.pass)) {
        return [string]$baselineMetadata.pass
      }
    } catch {
      # Fall through to historical manifests.
    }
  }

  $manifestRoot = Join-Path $Root 'manifests'
  if(Test-Path -LiteralPath $manifestRoot) {
    $bestPass = $null
    $bestScore = [int64]::MinValue
    foreach($manifest in Get-ChildItem -LiteralPath $manifestRoot -Filter 'cumulative_patch_manifest_pass*.json' -File -ErrorAction SilentlyContinue) {
      try {
        $candidate = (Get-Content -LiteralPath $manifest.FullName -Raw | ConvertFrom-Json).pass
        if($candidate -match '^(\d+)Z(\d+)(?:([A-Za-z]+)(\d+)([A-Za-z]*)(?:\.(\d+))?)?$') {
          $score = ([int64]$Matches[1] * 1000000000000000L) + ([int64]$Matches[2] * 1000000000L)
          if(-not [string]::IsNullOrWhiteSpace($Matches[4])) {
            $score += [int64]$Matches[4] * 10000L
          }
          if(-not [string]::IsNullOrWhiteSpace($Matches[5])) {
            $suffix = $Matches[5].ToUpperInvariant()
            $suffixScore = 0L
            foreach($char in $suffix.ToCharArray()) {
              if($char -ge 'A' -and $char -le 'Z') {
                $suffixScore = ($suffixScore * 26L) + ([int][char]$char - [int][char]'A' + 1)
              }
            }
            $score += $suffixScore * 100L
          }
          if(-not [string]::IsNullOrWhiteSpace($Matches[6])) {
            $score += [int64]$Matches[6]
          }
        } else {
          continue
        }
        if($score -gt $bestScore) {
          $bestScore = $score
          $bestPass = $candidate
        }
      } catch {
        # A malformed historical manifest must not block packaging current source.
      }
    }
    if(-not [string]::IsNullOrWhiteSpace($bestPass)) {
      return $bestPass
    }
  }

  return 'manual'
}

$current = Get-Snapshot
$effectivePass = Resolve-EffectivePass
if($Mode -eq 'baseline') {
  Save-Baseline -Files $current -BaselinePass $effectivePass
  exit 0
}

$name = if($Mode -eq 'patch') {
  "Havenwild_IncrementalPatch_Pass$effectivePass`_$handoffStamp.zip"
} elseif($Mode -eq 'handoff') {
  $baselinePass = 'unknown'
  if(Test-Path -LiteralPath $baselinePath) {
    try {
      $baselineMetadata = Get-Content -LiteralPath $baselinePath -Raw | ConvertFrom-Json
      if(-not [string]::IsNullOrWhiteSpace([string]$baselineMetadata.pass)) {
        $baselinePass = [string]$baselineMetadata.pass
      }
    } catch {
      # The explicit baseline existence/shape gate below will report a useful error.
    }
  }
  "Havenwild_DevelopmentHandoff_FromPass$baselinePass`_ToPass$effectivePass`_$handoffStamp.zip"
} else {
  "Havenwild_CompleteSourceRollup_Pass$effectivePass`_$stamp.zip"
}
$out = Join-Path $outDir $name
if(Test-Path -LiteralPath $out) { Remove-Item -LiteralPath $out -Force }

$staging = Join-Path $env:TEMP ("havenwild-package-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path $staging | Out-Null

try {
  $included = @()
  $removed = @()

  if($Mode -in @('patch','handoff')) {
    if(-not (Test-Path -LiteralPath $baselinePath)) {
      throw 'No package baseline exists. Use Packaging & Baselines > Capture package baseline after applying the current accepted source, then create the incremental patch or development handoff.'
    }

    $baselineMetadata = Get-Content -LiteralPath $baselinePath -Raw | ConvertFrom-Json
    $baseline = $baselineMetadata.files
    $baselinePass = if([string]::IsNullOrWhiteSpace([string]$baselineMetadata.pass)) { 'legacy-local-baseline' } else { [string]$baselineMetadata.pass }
    $baseMap = @{}
    foreach($property in $baseline.PSObject.Properties) {
      $baseMap[$property.Name] = $property.Value
    }

    foreach($relative in $current.Keys) {
      if((-not $baseMap.ContainsKey($relative)) -or
         ($baseMap[$relative].sha256 -ne $current[$relative].sha256)) {
        $included += $relative
      }
    }
    foreach($relative in $baseMap.Keys) {
      if(-not $current.Contains($relative)) { $removed += $relative }
    }

    # Development handoffs retain the historical self-contained bootstrap set.
    # Root-drop incremental patches are intentionally minimal and contain only
    # files changed relative to the captured package baseline.
    if($Mode -eq 'handoff') {
      $bootstrapFiles = @(
        'HavenwildTools.cmd',
        'tools/control/HavenwildTools.ps1',
        'tools/control/ApplyPatchRemovals.ps1',
        'tools/control/ProjectCommandRegistry.ps1'
      )
      foreach($relative in $bootstrapFiles) {
        if($current.ContainsKey($relative) -and -not ($included -contains $relative)) {
          $included += $relative
        }
      }
    }

    foreach($relative in $included) {
      $nativeRelative = $relative.Replace('/', [System.IO.Path]::DirectorySeparatorChar)
      $src = Join-Path $Root $nativeRelative
      $dst = Join-Path $staging $nativeRelative
      New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst) | Out-Null
      Copy-Item -LiteralPath $src -Destination $dst -Force
    }

    if($Mode -eq 'handoff') {
      $removalDir = Join-Path $staging 'manifests\removals'
      New-Item -ItemType Directory -Force -Path $removalDir | Out-Null
      $removalText = if($removed.Count -gt 0) { ($removed -join [Environment]::NewLine) + [Environment]::NewLine } else { '' }
      Write-Utf8NoBom -Path (Join-Path $removalDir 'PATCH_REMOVALS.txt') -Text $removalText
    }
  } else {
    $packageFiles = if($Mode -eq 'rollup') { @(Get-RollupProjectFiles) } else { @(Get-ProjectFiles) }
    foreach($file in $packageFiles) {
      $relative = Convert-ToProjectRelativePath -FullName $file.FullName
      $nativeRelative = $relative.Replace('/', [System.IO.Path]::DirectorySeparatorChar)
      $dst = Join-Path $staging $nativeRelative
      New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst) | Out-Null
      Copy-Item -LiteralPath $file.FullName -Destination $dst -Force
      $included += $relative
    }
  }

  if($Mode -eq 'patch') {
    if($included.Count -eq 0 -and $removed.Count -eq 0) {
      throw 'No source changes exist relative to the captured package baseline.'
    }

    $patchFiles = @()
    foreach($relative in $included) {
      $metadata = $current[$relative]
      $patchFiles += [ordered]@{
        path = $relative
        sha256 = [string]$metadata.sha256
        bytes = [int64]$metadata.bytes
      }
    }
    $patchManifest = [ordered]@{
      schema = 'havenwild.root_patch.v1'
      project = 'Havenwild'
      patchId = ("Pass{0}-{1}" -f $effectivePass,$handoffStamp)
      pass = $effectivePass
      applyMode = 'overwrite'
      createdUtc = (Get-Date).ToUniversalTime().ToString('o')
      baselinePass = $baselinePass
      files = @($patchFiles)
      remove = @($removed)
    }
    $patchManifestJson = ($patchManifest | ConvertTo-Json -Depth 8) + [Environment]::NewLine
    Write-Utf8NoBom -Path (Join-Path $staging 'PATCH_MANIFEST.json') -Text $patchManifestJson
  } else {
    $manifestDir = Join-Path $staging 'manifests\packages'
    New-Item -ItemType Directory -Force -Path $manifestDir | Out-Null
    $packageManifest = [ordered]@{
      version = 3
      mode = $Mode
      pass = $effectivePass
      createdUtc = (Get-Date).ToUniversalTime().ToString('o')
      sourcePolicy = $(if($Mode -eq 'rollup') { 'havenwild_reproducible_lean_source_v1' } else { 'havenwild_owned_source_only' })
      purpose = $(if($Mode -eq 'handoff') { 'development_handoff_only' } else { 'project_package' })
      officialCumulativePass = $false
      baselinePass = $(if($Mode -eq 'handoff') { $baselinePass } else { $null })
      note = $(if($Mode -eq 'handoff') { 'Upload this ZIP to the Havenwild project chat to synchronize local editor-authored source changes. It is not an official cumulative overwrite pass.' } else { '' })
      excludedRoots = $excludedRootNames
      excludedPrefixes = $excludedPathPrefixes
      rollupPolicy = $(if($Mode -eq 'rollup') { 'content/architecture/havenwild_source_rollup_policy_v1.json' } else { $null })
      rollupExcludedPrefixes = $(if($Mode -eq 'rollup') { @($rollupExcludedPrefixes) } else { @() })
      rollupExcludedExactPaths = $(if($Mode -eq 'rollup') { @($rollupExcludedExactPaths) } else { @() })
      rollupAlwaysRetainPrefixes = $(if($Mode -eq 'rollup') { @($rollupAlwaysRetainPrefixes) } else { @() })
      included = @($included)
      removed = @($removed)
    }
    $packageManifestJson = ($packageManifest | ConvertTo-Json -Depth 8) + [Environment]::NewLine
    Write-Utf8NoBom -Path (Join-Path $manifestDir "Pass$effectivePass-package.json") -Text $packageManifestJson
  }

  Invoke-StagingZip -SourceDirectory $staging -DestinationZip $out
  $hash = (Get-FileHash $out -Algorithm SHA256).Hash.ToLowerInvariant()
  $hashPath = "$out.sha256"
  "$hash  $([System.IO.Path]::GetFileName($out))" | Set-Content -LiteralPath $hashPath -Encoding ASCII

  $latestSourcePointer = $null
  if($Mode -eq 'rollup') {
    $latestSourcePointer = Join-Path $outDir 'LATEST_SOURCE_ROLLUP.txt'
    $pointerLines = @(
      "Havenwild lean complete source rollup"
      "Path: $out"
      "Checksum: $hashPath"
      "SHA-256: $hash"
      "Pass: $effectivePass"
      "Included: $($included.Count)"
      "CreatedUtc: $((Get-Date).ToUniversalTime().ToString('o'))"
    )
    ($pointerLines -join [Environment]::NewLine) + [Environment]::NewLine |
      Set-Content -LiteralPath $latestSourcePointer -Encoding UTF8
  }

  Write-Host "Created: $out"
  Write-Host "Checksum: $hashPath"
  if($null -ne $latestSourcePointer) {
    Write-Host "Latest source pointer: $latestSourcePointer"
  }
  Write-Host "Included: $($included.Count)"
  Write-Host "Removed: $($removed.Count)"
  Write-Host "SHA-256: $hash"
} finally {
  if(Test-Path -LiteralPath $staging) {
    Remove-Item -LiteralPath $staging -Recurse -Force
  }
}
