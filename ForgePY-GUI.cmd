@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

where py >nul 2>nul
if not errorlevel 1 (
  py -3 -c "import sys, tkinter; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
  if not errorlevel 1 (
    where pyw >nul 2>nul
    if not errorlevel 1 (
      start "" pyw -3 "%~dp0.forgepy\gui\pcc_gui.py" --root "%CD%"
      exit /b 0
    )
    py -3 "%~dp0.forgepy\gui\pcc_gui.py" --root "%CD%"
    exit /b %errorlevel%
  )
)

where python >nul 2>nul
if not errorlevel 1 (
  python -c "import sys, tkinter; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
  if not errorlevel 1 (
    where pythonw >nul 2>nul
    if not errorlevel 1 (
      start "" pythonw "%~dp0.forgepy\gui\pcc_gui.py" --root "%CD%"
      exit /b 0
    )
    python "%~dp0.forgepy\gui\pcc_gui.py" --root "%CD%"
    exit /b %errorlevel%
  )
)

echo [WARN] Tk GUI runtime is unavailable. Falling back to the console PCC.
call "%~dp0ForgePY.cmd" menu
exit /b %errorlevel%
