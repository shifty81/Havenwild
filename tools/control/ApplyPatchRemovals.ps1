[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$Root,
  [string]$Manifest=''
)

$ErrorActionPreference = 'Stop'
$rootResolved = (Resolve-Path -LiteralPath $Root).Path
$rootFull = [IO.Path]::GetFullPath($rootResolved).TrimEnd('\')
$rootPrefix = $rootFull + '\'
$manifestPath = if ($Manifest) { $Manifest } else { Join-Path $rootFull 'manifests\removals\PATCH_REMOVALS.txt' }

if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
  Write-Host 'No removal manifest found.'
  return
}

$entries = @()
foreach ($line in Get-Content -LiteralPath $manifestPath) {
  $relative = ([string]$line).Trim()
  if (-not $relative -or $relative.StartsWith('#') -or $relative.StartsWith(';')) { continue }

  $target = [IO.Path]::GetFullPath((Join-Path $rootFull $relative))
  if ($target.Equals($rootFull, [StringComparison]::OrdinalIgnoreCase) -or
      -not $target.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Unsafe removal path: $relative"
  }

  $depth = ($relative -split '[\\/]').Count
  $entries += [pscustomobject]@{ Relative=$relative; Target=$target; Depth=$depth }
}

# Remove the deepest paths first.  This avoids asking Remove-Item -Recurse to
# own the entire cleanup when a manifest also contains explicit child paths.
$removed = 0
$failures = @()
$orderedEntries = @($entries | Sort-Object -Property Depth -Descending)
foreach ($entry in $orderedEntries) {
  if (-not (Test-Path -LiteralPath $entry.Target)) { continue }
  try {
    Remove-Item -LiteralPath $entry.Target -Recurse -Force -ErrorAction Stop
    $removed++
  } catch {
    $failures += ("{0}: {1}" -f $entry.Relative, $_.Exception.Message)
  }
}

if ($failures.Count -gt 0) {
  Write-Host ("Patch removals completed with {0} failure(s); {1} path(s) removed." -f $failures.Count, $removed) -ForegroundColor Yellow
  foreach ($failure in $failures) { Write-Host ("  {0}" -f $failure) -ForegroundColor Yellow }
  throw ("Patch cleanup left {0} path(s) unresolved. The manifest has been retained for retry." -f $failures.Count)
}

Write-Host ("Patch removals applied: {0}" -f $removed)
