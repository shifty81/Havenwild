Set-StrictMode -Version 2.0

function Get-PccCommandRegistry {
  param([Parameter(Mandatory=$true)][string]$Root)
  $base=@(& (Join-Path $Root 'tools\control\ProjectCommandRegistry.ps1'))
  $extPath=Join-Path $Root 'tools\control\PccCommandExtensions.ps1'
  $ext=@()
  if(Test-Path -LiteralPath $extPath -PathType Leaf){ $ext=@(& $extPath) }
  return @($base + $ext)
}


function Get-PccPythonCommand {
  $python=Get-Command python -ErrorAction SilentlyContinue
  if($null -eq $python){ $python=Get-Command py -ErrorAction SilentlyContinue }
  return $python
}

function Test-PccCommandKey {
  param([string]$Root,[string]$Key)
  if([string]::IsNullOrWhiteSpace($Key)){ return $false }
  return ($null -ne (Get-PccCommandRegistry -Root $Root | Where-Object { [string]$_.Key -eq $Key } | Select-Object -First 1))
}

function Invoke-PccLegacyCommand {
  param([string]$Root,[string]$Key,[string]$Pass='manual')
  $legacy=Join-Path $Root 'tools\control\HavenwildTools.ps1'
  # Do not let the caller's `$code = Invoke-PccLegacyCommand ...` assignment
  # capture the legacy control center's success stream. Converting each child
  # line to host output here keeps Full/Fast Gate, Cargo, tests, and validators
  # visible in real time while this function returns only the numeric exit code.
  & powershell -NoProfile -ExecutionPolicy Bypass -File $legacy -Command $Key -Pass $Pass 2>&1 |
    ForEach-Object { Write-Host $_ }
  $code=$LASTEXITCODE
  if($null -eq $code){ $code=0 }
  return [int]$code
}

function Invoke-PccBuiltinCommand {
  param([string]$Root,[string]$Key)
  $python=Get-PccPythonCommand
  if($null -eq $python){ Write-Host 'PCC builtin commands require Python.' -ForegroundColor Red; return 2 }
  switch($Key){
    'pcc.status' {
      & $python.Source (Join-Path $Root 'tools\control\PccQuickState.py') '--root' $Root '--pretty'
      return $LASTEXITCODE
    }
    'pcc.patch-ledger' {
      $path=Join-Path $Root '.havenwild\pcc\patch-ledger.json'
      if(Test-Path -LiteralPath $path){ Get-Content -LiteralPath $path } else { Write-Host 'No PCC patch ledger exists yet.' }
      return 0
    }
    'pcc.capabilities' {
      & $python.Source (Join-Path $Root 'tools\forge\HavenwildPccProvider.py') 'capabilities' '--root' $Root
      return $LASTEXITCODE
    }
    'pcc.validate-v2' {
      & $python.Source (Join-Path $Root 'tools\validation\Validate-HavenwildPccV2.py') '--root' $Root
      return $LASTEXITCODE
    }
    'pcc.validate-lifecycle' {
      & $python.Source (Join-Path $Root 'tools\validation\Validate-HavenwildPccLifecycle.py') '--root' $Root
      return $LASTEXITCODE
    }
    'pcc.validate-editor-v2' {
      & $python.Source (Join-Path $Root 'tools\validation\Validate-HavenwildEditorArchitectureV2.py') '--root' $Root
      return $LASTEXITCODE
    }
    'pcc.vault-status' {
      & $python.Source (Join-Path $Root 'tools\control\PccVaultAdapter.py') 'status' '--root' $Root '--pretty'
      return $LASTEXITCODE
    }
    'pcc.vault-sync' {
      & $python.Source (Join-Path $Root 'tools\control\PccVaultAdapter.py') 'sync' '--root' $Root '--pretty'
      return $LASTEXITCODE
    }
  }
  Write-Host "Unsupported PCC builtin command: $Key" -ForegroundColor Yellow
  return 2
}

function Invoke-PccCommandKey {
  param([string]$Root,[string]$Key,[string]$Pass='manual')
  # Registered candidate operations are dispatched by the SAME PCC job host.
  # Do not forward these extension keys to HavenwildTools.ps1: its historical
  # registry intentionally does not include the extension registry.
  if($Key -in @('experimental.bevy.status','experimental.bevy.verify','experimental.bevy.scene-plan','experimental.bevy.draft-plan','experimental.bevy.build','experimental.bevy.run')) {
    $action=switch($Key){
      'experimental.bevy.status' { 'Status' }
      'experimental.bevy.verify' { 'Verify' }
      'experimental.bevy.scene-plan' { 'ScenePlan' }
      'experimental.bevy.draft-plan' { 'DraftPlan' }
      'experimental.bevy.build' { 'Build' }
      'experimental.bevy.run' { 'Run' }
    }
    $script=Join-Path $Root 'tools\control\HavenwildBevyCandidate.ps1'
    & powershell -NoProfile -ExecutionPolicy Bypass -File $script -Root $Root -Action $action
    $result=$LASTEXITCODE
    if($null -eq $result){ return 2 }
    return [int]$result
  }
  if($Key.StartsWith('pcc.')){ return Invoke-PccBuiltinCommand -Root $Root -Key $Key }
  return Invoke-PccLegacyCommand -Root $Root -Key $Key -Pass $Pass
}
