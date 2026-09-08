@echo off
setlocal
cd /d "%~dp0"

set "SHORE=crates\haven_world\src\autotile\shoreline_resolver_tests.rs"
set "COAST=crates\haven_world\src\island_coastline.rs"

if not exist "%SHORE%" (
  echo ERROR: Missing %SHORE%
  exit /b 1
)
if not exist "%COAST%" (
  echo ERROR: Missing %COAST%
  exit /b 1
)

findstr /C:"assert!(report.unsupported_shapes_repaired > 0)" "%SHORE%" >nul
if not errorlevel 1 (
  echo ERROR: Stale checkerboard counter assertion is still present.
  exit /b 1
)

findstr /C:"missing scene slot cell {x},{y} must remain semantic open water" "%COAST%" >nul
if errorlevel 1 (
  echo ERROR: Semantic open-water assertion is missing.
  exit /b 1
)

findstr /C:"use crate::autotile::terrain_family::TerrainFamily;" "%COAST%" >nul
if errorlevel 1 (
  echo ERROR: Test-only TerrainFamily import is missing.
  exit /b 1
)

echo PASS: Pass 161D6R1 source files are active in this folder.
exit /b 0
