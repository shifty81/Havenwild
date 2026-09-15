Set-StrictMode -Version 2.0
Add-Type -AssemblyName System.IO.Compression.FileSystem

function Get-PccPatchPatterns {
  return @('Havenwild_IncrementalPatch_*.zip','Havenwild_Patch_*.zip','Havenwild_Handoff_*.zip','Havenwild__*.patch','Havenwild_Patch_*.patch','HW-*.patch')
}

function Get-PccPendingPatchFiles {
  param([Parameter(Mandatory=$true)][string]$Root)
  $map=@{}
  foreach($pattern in @(Get-PccPatchPatterns)){
    foreach($f in @(Get-ChildItem -LiteralPath $Root -File -Filter $pattern -ErrorAction SilentlyContinue)){ $map[$f.FullName.ToLowerInvariant()]=$f }
  }
  return @($map.Values | Sort-Object LastWriteTime,Name)
}

function Get-PccCurrentBranch {
  param([Parameter(Mandatory=$true)][string]$Root)
  $branch=(@(& git -C $Root symbolic-ref --quiet --short HEAD 2>$null) -join '').Trim()
  if($LASTEXITCODE -ne 0){ return '' }
  return $branch
}

function Get-PccPatchTarget {
  param([Parameter(Mandatory=$true)][IO.FileInfo]$Patch)
  $lane=''; $branch=''; $required=$false
  if($Patch.Extension -ieq '.zip'){
    $archive=[IO.Compression.ZipFile]::OpenRead($Patch.FullName)
    try {
      $entry=@($archive.Entries | Where-Object { $_.FullName.Replace('\','/') -ieq 'PATCH_MANIFEST.json' } | Select-Object -First 1)
      if($entry.Count -gt 0){
        $reader=New-Object IO.StreamReader($entry[0].Open(),[Text.Encoding]::UTF8,$true)
        try { $manifest=($reader.ReadToEnd() | ConvertFrom-Json) } finally { $reader.Dispose() }
        if($null -ne $manifest.PSObject.Properties['targetLane']){ $lane=[string]$manifest.targetLane }
        if($null -ne $manifest.PSObject.Properties['targetBranch']){ $branch=[string]$manifest.targetBranch }
        if($null -ne $manifest.PSObject.Properties['required']){ $required=[bool]$manifest.required }
      }
    } finally { $archive.Dispose() }
  } else {
    foreach($line in @(Get-Content -LiteralPath $Patch.FullName -TotalCount 40 -ErrorAction SilentlyContinue)){
      if($line -match '^#\s*Havenwild-Target-Lane\s*:\s*(.+?)\s*$'){ $lane=$Matches[1].Trim() }
      elseif($line -match '^#\s*Havenwild-Target-Branch\s*:\s*(.+?)\s*$'){ $branch=$Matches[1].Trim() }
      elseif($line -match '^#\s*Havenwild-Required\s*:\s*(true|1|yes)\s*$'){ $required=$true }
    }
  }
  if([string]::IsNullOrWhiteSpace($lane) -and $branch -eq 'experimental'){ $lane='experimental' }
  if([string]::IsNullOrWhiteSpace($lane) -and $branch -eq 'main'){ $lane='main' }
  return [pscustomobject]@{ Lane=$lane.ToLowerInvariant(); Branch=$branch; Required=$required }
}

function Invoke-PccPatchLanePreflight {
  param([Parameter(Mandatory=$true)][string]$Root,[Parameter(Mandatory=$true)][object[]]$Patches)
  if($Patches.Count -eq 0){ return [pscustomobject]@{ Switched=$false; TargetLane=''; Required=$false } }
  $targets=@()
  $required=$false
  foreach($patch in $Patches){
    $target=Get-PccPatchTarget -Patch $patch
    if(-not [string]::IsNullOrWhiteSpace($target.Lane)){ $targets += $target.Lane }
    if($target.Required){ $required=$true }
  }
  $targets=@($targets | Sort-Object -Unique)
  if($targets.Count -gt 1){ throw ("Pending patches target multiple lanes: {0}" -f ($targets -join ', ')) }
  if($targets.Count -eq 0){ return [pscustomobject]@{ Switched=$false; TargetLane=''; Required=$required } }
  $targetLane=[string]$targets[0]
  $branch=Get-PccCurrentBranch -Root $Root
  if($targetLane -eq 'experimental' -and $branch -eq 'main'){
    $laneScript=Join-Path $Root 'tools\control\DevelopmentLane.ps1'
    & powershell -NoProfile -ExecutionPolicy Bypass -File $laneScript -Root $Root -Action Toggle
    if($LASTEXITCODE -ne 0){ throw 'Unable to switch Main -> Experimental before patch application.' }
    $branch=Get-PccCurrentBranch -Root $Root
    if($branch -ne 'experimental'){ throw "Lane preflight expected experimental but active branch is '$branch'." }
    return [pscustomobject]@{ Switched=$true; TargetLane=$targetLane; Required=$required }
  }
  if($targetLane -eq 'main' -and $branch -eq 'experimental'){
    throw 'Main-targeted patch encountered while Experimental is active. Automatic Experimental -> Main switching is intentionally blocked.'
  }
  if($targetLane -eq 'experimental' -and $branch -ne 'experimental'){ throw "Patch targets Experimental but active branch is '$branch'." }
  if($targetLane -eq 'main' -and $branch -ne 'main'){ throw "Patch targets Main but active branch is '$branch'." }
  return [pscustomobject]@{ Switched=$false; TargetLane=$targetLane; Required=$required }
}
