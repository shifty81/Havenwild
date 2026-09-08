@echo off
setlocal EnableExtensions
for %%I in ("%~dp0..\..") do set "ROOT=%%~fI"
set "PAUSE_ON_EXIT=0"
if "%~1"=="" set "PAUSE_ON_EXIT=1"
pushd "%ROOT%" >nul || (echo Unable to enter Havenwild repository root: "%ROOT%"& exit /b 1)
set "BASH_EXE="
if defined HAVENWILD_BASH if exist "%HAVENWILD_BASH%" set "BASH_EXE=%HAVENWILD_BASH%"
if not defined BASH_EXE if exist "%ProgramFiles%\Git\bin\bash.exe" set "BASH_EXE=%ProgramFiles%\Git\bin\bash.exe"
if not defined BASH_EXE if exist "%ProgramFiles%\Git\usr\bin\bash.exe" set "BASH_EXE=%ProgramFiles%\Git\usr\bin\bash.exe"
if not defined BASH_EXE if exist "%ProgramFiles(x86)%\Git\bin\bash.exe" set "BASH_EXE=%ProgramFiles(x86)%\Git\bin\bash.exe"
if not defined BASH_EXE if exist "%LocalAppData%\Programs\Git\bin\bash.exe" set "BASH_EXE=%LocalAppData%\Programs\Git\bin\bash.exe"
if not defined BASH_EXE (
  echo Git Bash was not found.
  echo Install Git for Windows or set HAVENWILD_BASH to the full path of bash.exe.
  popd >nul
  exit /b 1
)
"%BASH_EXE%" "./tools/build/Build.sh" %*
set "RESULT=%ERRORLEVEL%"
popd >nul
if "%PAUSE_ON_EXIT%"=="1" (
  echo.
  if not "%RESULT%"=="0" (echo Havenwild build failed with exit code %RESULT%.) else (echo Havenwild build completed successfully.)
  echo Build logs are stored under "%ROOT%\logs\builds".
  pause
)
exit /b %RESULT%
