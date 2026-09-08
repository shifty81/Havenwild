@echo off
setlocal EnableExtensions
for %%I in ("%~dp0..\..\..") do set "ROOT=%%~fI"
cd /d "%ROOT%" || exit /b 1
python tools\automation\characters\Build-UniversalLpcUsageManifestV167X.py %*
set "EXIT_CODE=%ERRORLEVEL%"
endlocal & exit /b %EXIT_CODE%
