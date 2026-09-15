@echo off
setlocal EnableExtensions
set "ROOT=%~dp0"
set "HOST=%ROOT%tools\control\HavenwildPccHost.ps1"
if not exist "%HOST%" (
  echo Havenwild PCC v2 host is missing: "%HOST%"
  exit /b 2
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%HOST%" %*
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo.
  echo Havenwild Tools failed to start or exited with code %RC%.
  echo See the newest log under "%ROOT%logs\sessions" if one was created.
  echo.
  pause
)
exit /b %RC%
