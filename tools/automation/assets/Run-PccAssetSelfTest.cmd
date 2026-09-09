@echo off
setlocal EnableExtensions
set "ASSET_DIR=%~dp0"
echo ========================================================================
echo  PCC UNIVERSAL ASSET SYSTEM SELF-TEST
echo ========================================================================
call "%ASSET_DIR%Run-PccAssetTool.cmd" self-test --output "%TEMP%\pcc-assets-selftest.json"
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
  type "%TEMP%\pcc-assets-selftest.json"
  echo.
  echo [PASS] PCC universal asset system self-test
) else (
  echo [FAIL] PCC universal asset system self-test exited with code %RC%.
)
echo.
pause
exit /b %RC%
