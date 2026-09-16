@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

where py >nul 2>nul
if not errorlevel 1 (
  py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
  if not errorlevel 1 (
    py -3 "%~dp0.forgepy\runtime\forgepy.py" --root "%CD%" %*
    exit /b %errorlevel%
  )
)

where python >nul 2>nul
if not errorlevel 1 (
  python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
  if not errorlevel 1 (
    python "%~dp0.forgepy\runtime\forgepy.py" --root "%CD%" %*
    exit /b %errorlevel%
  )
)

echo [FAIL] Python 3.10+ was not found. Install Python 3.10 or newer and place it on PATH.
exit /b 127
