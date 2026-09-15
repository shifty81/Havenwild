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
  & powershell -NoProfile -ExecutionPolicy Bypass -File $legacy -Command $Key -Pass $Pass
  return $LASTEXITCODE
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
  }
  Write-Host "Unsupported PCC builtin command: $Key" -ForegroundColor Yellow
  return 2
}

function Invoke-PccCommandKey {
  param([string]$Root,[string]$Key,[string]$Pass='manual')
  if($Key.StartsWith('pcc.')){ return Invoke-PccBuiltinCommand -Root $Root -Key $Key }
  return Invoke-PccLegacyCommand -Root $Root -Key $Key -Pass $Pass
}
