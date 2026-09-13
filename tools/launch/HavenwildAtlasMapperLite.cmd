@echo off
setlocal EnableExtensions

set "ROOT=%~dp0..\.."
for %%I in ("%ROOT%") do set "ROOT=%%~fI"

if not exist "%ROOT%\Cargo.toml" (
  echo Havenwild Atlas Mapper Lite launcher could not find Cargo.toml.
  echo Resolved root: "%ROOT%"
  echo This launcher must remain under tools\launch inside the Havenwild repository.
  echo.
  pause
  exit /b 101
)

where cargo >nul 2>nul
if errorlevel 1 (
  echo Cargo was not found on PATH.
  echo Run the Havenwild PCC preflight/full gate first or open a shell with Rust installed.
  echo.
  pause
  exit /b 102
)

pushd "%ROOT%" >nul
cargo run -p haven_atlas_mapper_lite -- %*
set "RC=%ERRORLEVEL%"
popd >nul

if not "%RC%"=="0" (
  echo.
  echo Havenwild Atlas Mapper Lite failed or exited with code %RC%.
  echo Run the PCC full gate before committing this tool.
  echo.
  pause
)
exit /b %RC%
