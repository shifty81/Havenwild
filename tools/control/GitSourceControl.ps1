# Canonical Havenwild Git bridge (CC8E16).
# Intentionally no param(...) block: accepts current and legacy Control Center
# argument shapes without parameter-binding drift.
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$action = 'Status'
$message = ''
$remote = ''
$positionals = New-Object System.Collections.Generic.List[string]

for($i=0; $i -lt $args.Count; $i++) {
  $raw = [string]$args[$i]
  $key = $raw.TrimStart('-').ToLowerInvariant()
  if($key -in @('root','projectroot','repositoryroot') -and ($i+1) -lt $args.Count) { $root = [string]$args[++$i]; continue }
  if($key -eq 'action' -and ($i+1) -lt $args.Count) { $action = [string]$args[++$i]; continue }
  if($key -in @('message','commitmessage') -and ($i+1) -lt $args.Count) { $message = [string]$args[++$i]; continue }
  if($key -in @('remote','remoteurl','url') -and ($i+1) -lt $args.Count) { $remote = [string]$args[++$i]; continue }
  if(-not $raw.StartsWith('-')) { $positionals.Add($raw) }
}

if($positionals.Count -gt 0 -and (Test-Path -LiteralPath $positionals[0])) { $root = $positionals[0] }
$known = @('Status','Setup','Init','Initialize','Connect','Repair','Adopt','Review','ReviewCore','ReviewGitHubCore','CommitGreen','CommitPushGreen','Push','PushMain','Pull','Open','OpenRepo','CommitManual','ManualCommit','AdvancedCommit')
foreach($p in $positionals) { if($known -contains $p) { $action = $p; break } }

$python = Get-Command python -ErrorAction SilentlyContinue
if($null -eq $python){ $python = Get-Command py -ErrorAction SilentlyContinue }
if($null -eq $python){ throw 'Canonical Havenwild source-control authority requires Python, but Python was not found.' }

# CC8E16: Setup is no longer a blind git-init/fetch operation. A GitHub Download ZIP
# can already contain a valuable hydrated/validated working tree, so connect/repair
# adopts origin/main history with git reset --mixed while proving governed file bytes
# did not change. Divergent local history is backed up before adoption.
$normalizedAction = $action.Trim().ToLowerInvariant().Replace('-','').Replace('_','')
if($normalizedAction -in @('setup','init','initialize','connect','repair','adopt')) {
  $repair = Join-Path $PSScriptRoot 'RepairGitWorkingCopy.py'
  if(-not (Test-Path -LiteralPath $repair -PathType Leaf)) { throw "Git working-folder repair authority is missing: $repair" }
  $repairArgs = @($repair,'--root',$root)
  if(-not [string]::IsNullOrWhiteSpace($remote)) { $repairArgs += @('--remote',$remote) }
  & $python.Source @repairArgs
  exit $LASTEXITCODE
}

$authority = Join-Path $PSScriptRoot 'HavenwildGateAuthority.py'
if(-not (Test-Path -LiteralPath $authority)){ throw "Canonical Havenwild source-control authority is missing: $authority" }

$callArgs = @($authority,'git','--root',$root,'--action',$action)
if(-not [string]::IsNullOrWhiteSpace($message)){ $callArgs += @('--message',$message) }
if(-not [string]::IsNullOrWhiteSpace($remote)){ $callArgs += @('--remote',$remote) }
& $python.Source @callArgs
exit $LASTEXITCODE
