param([Parameter(Mandatory=$true)][string]$Root)
$ErrorActionPreference='Stop'

# Root audit is intentionally side-effect free. Incremental root-patch intake is
# owned by the Full quality gate before this validator runs. Packaging, baseline
# capture, and standalone diagnostics may call this audit without mutating source.
#
# Keep required project authority separate from optional governed metadata. Git
# integration may legitimately add repository-control files such as .gitattributes
# without making those files mandatory for every checkout/worktree.
$required=@('.gitignore','Cargo.lock','Cargo.toml','README.md','HavenwildTools.cmd')
# These four launchers are committed project files (B48R16), not transient
# root-drop update transports. Keep the allowlist explicit rather than allowing
# every *.cmd, so arbitrary scripts and unpacked/renamed patch files still fail.
$optional=@('.gitattributes','.gitmodules','ForgePY-GUI.cmd','ForgePY-Install.cmd','ForgePY-Verify.cmd','ForgePY.cmd')
$allowed=@($required + $optional)

$files=Get-ChildItem -LiteralPath $Root -File | Select-Object -ExpandProperty Name
$unexpected=@($files | Where-Object { $_ -notin $allowed })
$missing=@($required | Where-Object { $_ -notin $files })
Write-Host "Root file count: $($files.Count)"
if($unexpected.Count -eq 0 -and $missing.Count -eq 0){
  Write-Host 'PASS: root contains only required project authority and governed optional metadata.'
  exit 0
}
if($unexpected.Count){Write-Host 'FAIL: unexpected root files:';$unexpected|ForEach-Object{Write-Host " - $_"}}
if(@($unexpected | Where-Object { $_ -match '^Havenwild_CUMULATIVE_PCC_Patch_.+ \([0-9]+\)\.zip$' }).Count -gt 0){
  Write-Host 'RECOVERY: browser-renamed duplicate cumulative ZIP (1).zip is not a normal transport. Preserve it outside the root (e.g. Downloads) or re-run PCC with repaired duplicate holding logic. Do not extract it into the repository.'
}

if($missing.Count){Write-Host 'FAIL: missing required root files:';$missing|ForEach-Object{Write-Host " - $_"}}
exit 1
