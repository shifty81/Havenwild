@echo off
setlocal
set "SCRIPT=%~dp0Apply-W60E3A-CompileRepair.py"
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  py -3 "%SCRIPT%"
) else (
  python "%SCRIPT%"
)
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo.
  echo W60E3A compile repair FAILED with exit code %RC%.
  exit /b %RC%
)
echo.
echo W60E3A compile repair complete.
exit /b 0
