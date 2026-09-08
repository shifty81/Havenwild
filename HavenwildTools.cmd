@echo off
setlocal EnableExtensions
set "ROOT=%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%tools\control\HavenwildTools.ps1" %*
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo.
  echo Havenwild Tools failed to start or exited with code %RC%.
  echo See the newest log under "%ROOT%logs\sessions" if one was created.
  echo.
  pause
)
exit /b %RC%
