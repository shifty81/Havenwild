@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "PYTHONUNBUFFERED=1"

rem The GUI entrypoint must never start a console-subsystem interpreter.
rem pyw/pythonw are windowless; the GUI pipes an unbuffered python.exe backend.
where py >nul 2>nul
if not errorlevel 1 (
  py -3 -c "import sys, tkinter; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
  if not errorlevel 1 (
    where pyw >nul 2>nul
    if not errorlevel 1 (
      start "" pyw -3 "%~dp0.forgepy\gui\pcc_gui.py" --root "%CD%"
      exit /b %errorlevel%
    )
  )
)

where python >nul 2>nul
if not errorlevel 1 (
  python -c "import sys, tkinter; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
  if not errorlevel 1 (
    where pythonw >nul 2>nul
    if not errorlevel 1 (
      start "" pythonw "%~dp0.forgepy\gui\pcc_gui.py" --root "%CD%"
      exit /b %errorlevel%
    )
  )
)

echo [FAIL] ForgePY GUI requires Tk and Python 3.10+ with pyw.exe or pythonw.exe.
echo For the explicit console interface, run ForgePY.cmd menu.
exit /b 127
