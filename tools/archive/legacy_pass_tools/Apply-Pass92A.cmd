@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python was not found in PATH.
  exit /b 1
)
python tools/automation/assets\Apply-IncorrectGameplayToolAtlasRemovalPass92A.py
exit /b %errorlevel%
