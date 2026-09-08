@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
py -3 "%SCRIPT_DIR%Build-LpcEcosystemIntakeR18R28.py" %*
if errorlevel 1 exit /b %errorlevel%
endlocal
