@echo off
setlocal EnableExtensions
set "ASSET_DIR=%~dp0"
for %%I in ("%ASSET_DIR%\..\..\..") do set "ROOT=%%~fI"
pushd "%ROOT%"
where py >nul 2>nul
if %ERRORLEVEL%==0 (
  py -3 -m tools.automation.assets.pcc_assets %*
) else (
  python -m tools.automation.assets.pcc_assets %*
)
set "RC=%ERRORLEVEL%"
popd
exit /b %RC%
