@echo off
setlocal EnableExtensions
for %%I in ("%~dp0..\..") do set "ROOT=%%~fI"
set "PAUSE_ON_EXIT=0"
if "%~1"=="" set "PAUSE_ON_EXIT=1"
pushd "%ROOT%" >nul || (echo Unable to enter Havenwild repository root: "%ROOT%"& exit /b 1)

rem Current validation/test authority is Python v4. Intercept the generic
rem quality-gate commands here so the root control center cannot fall through
rem to historical pass-by-pass validators still preserved in Build.sh/Build.ps1.
set "PYTHON_EXE="
where python >nul 2>&1 && set "PYTHON_EXE=python"
if not defined PYTHON_EXE where py >nul 2>&1 && set "PYTHON_EXE=py"

if /I "%~1"=="test" goto current_test
if /I "%~1"=="validate" goto current_validate
if /I "%~1"=="certify" goto current_certify
if /I "%~1"=="framework-audit" goto current_framework

goto bash_dispatch

:require_python
if defined PYTHON_EXE exit /b 0
echo Python was not found.
echo Install Python or place python.exe/py.exe on PATH.
exit /b 1

:current_test
call :require_python
if errorlevel 1 (set "RESULT=1"& goto finish)
"%PYTHON_EXE%" "tools\automation\validation\check_current.py" source --cargo-test
set "RESULT=%ERRORLEVEL%"
goto finish

:current_validate
call :require_python
if errorlevel 1 (set "RESULT=1"& goto finish)
set "VALIDATION_PROFILE=%~2"
if not defined VALIDATION_PROFILE set "VALIDATION_PROFILE=source"
"%PYTHON_EXE%" "tools\automation\validation\check_current.py" "%VALIDATION_PROFILE%"
set "RESULT=%ERRORLEVEL%"
goto finish

:current_certify
call :require_python
if errorlevel 1 (set "RESULT=1"& goto finish)
"%PYTHON_EXE%" "tools\automation\validation\check_current.py" full
set "RESULT=%ERRORLEVEL%"
goto finish

:current_framework
call :require_python
if errorlevel 1 (set "RESULT=1"& goto finish)
"%PYTHON_EXE%" "tools\automation\validation\check_current.py" framework
set "RESULT=%ERRORLEVEL%"
goto finish

:bash_dispatch
set "BASH_EXE="
if defined HAVENWILD_BASH if exist "%HAVENWILD_BASH%" set "BASH_EXE=%HAVENWILD_BASH%"
if not defined BASH_EXE if exist "%ProgramFiles%\Git\bin\bash.exe" set "BASH_EXE=%ProgramFiles%\Git\bin\bash.exe"
if not defined BASH_EXE if exist "%ProgramFiles%\Git\usr\bin\bash.exe" set "BASH_EXE=%ProgramFiles%\Git\usr\bin\bash.exe"
if not defined BASH_EXE if exist "%ProgramFiles(x86)%\Git\bin\bash.exe" set "BASH_EXE=%ProgramFiles(x86)%\Git\bin\bash.exe"
if not defined BASH_EXE if exist "%LocalAppData%\Programs\Git\bin\bash.exe" set "BASH_EXE=%LocalAppData%\Programs\Git\bin\bash.exe"
if not defined BASH_EXE (
  echo Git Bash was not found.
  echo Install Git for Windows or set HAVENWILD_BASH to the full path of bash.exe.
  set "RESULT=1"
  goto finish
)
"%BASH_EXE%" "./tools/build/Build.sh" %*
set "RESULT=%ERRORLEVEL%"

:finish
popd >nul
if "%PAUSE_ON_EXIT%"=="1" (
  echo.
  if not "%RESULT%"=="0" (echo Havenwild build failed with exit code %RESULT%.) else (echo Havenwild build completed successfully.)
  echo Build logs are stored under "%ROOT%\logs\builds".
  pause
)
exit /b %RESULT%
