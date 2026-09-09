@echo off
setlocal EnableExtensions EnableDelayedExpansion
set "ASSET_DIR=%~dp0"
for %%I in ("%ASSET_DIR%\..\..\..") do set "ROOT=%%~fI"

rem -----------------------------------------------------------------------
rem CLI compatibility lane.
rem If arguments are supplied, behave exactly like a normal command-line
rem dispatcher: no prompts, no pause, and preserve the Python exit code.
rem -----------------------------------------------------------------------
if not "%~1"=="" (
  call :RUN_PCC %*
  exit /b %ERRORLEVEL%
)

rem -----------------------------------------------------------------------
rem Interactive lane.
rem Double-clicking Run-PccAssetTool.cmd now opens the universal asset menu.
rem -----------------------------------------------------------------------
:MENU
cls
echo ========================================================================
echo  PCC UNIVERSAL ASSET TOOLING
echo ========================================================================
echo  Repository : %ROOT%
echo  Adapter    : Havenwild / 32x32 default
echo ------------------------------------------------------------------------
echo   1. Run universal asset self-test
echo   2. Inventory existing Havenwild asset tooling
echo   3. Scan an asset folder into a canonical catalog
echo   4. Analyze one PNG sprite sheet
echo   5. Inspect Tiled TSX/TMX metadata
echo   6. Extract multi-tile prefab candidates from a catalog
echo   7. Generate a semantic house prefab recipe
echo   8. Validate an asset catalog
echo   9. Show CLI help
echo   0. Exit
echo ------------------------------------------------------------------------
set "CHOICE="
set /p "CHOICE=Select an option: "

if "%CHOICE%"=="1" goto :SELFTEST
if "%CHOICE%"=="2" goto :INVENTORY
if "%CHOICE%"=="3" goto :SCAN
if "%CHOICE%"=="4" goto :ANALYZE
if "%CHOICE%"=="5" goto :TILED
if "%CHOICE%"=="6" goto :PREFABS
if "%CHOICE%"=="7" goto :HOUSE
if "%CHOICE%"=="8" goto :VALIDATE
if "%CHOICE%"=="9" goto :HELP
if "%CHOICE%"=="0" exit /b 0

echo.
echo Invalid selection.
call :WAIT
goto :MENU

:SELFTEST
cls
echo ========================================================================
echo  PCC ASSET SELF-TEST
echo ========================================================================
set "OUT=%TEMP%\pcc-assets-selftest.json"
call :RUN_PCC self-test --output "%OUT%"
set "RC=%ERRORLEVEL%"
echo.
if exist "%OUT%" type "%OUT%"
echo.
if "%RC%"=="0" (
  echo [PASS] Universal asset self-test completed.
) else (
  echo [FAIL] Universal asset self-test exited with code %RC%.
)
call :WAIT
goto :MENU

:INVENTORY
cls
echo ========================================================================
echo  PCC ASSET TOOL NORMALIZATION INVENTORY
echo ========================================================================
set "OUT=%ROOT%\artifacts\asset-intake\legacy-tool-inventory.json"
call :RUN_PCC inventory-tools "%ROOT%" --output "%OUT%"
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
  echo [PASS] Inventory created:
  echo   %OUT%
) else (
  echo [FAIL] Inventory exited with code %RC%.
)
call :WAIT
goto :MENU

:SCAN
cls
echo ========================================================================
echo  PCC ASSET FOLDER SCAN
echo ========================================================================
echo Enter the folder to scan.
echo Example:
echo   assets\source\licensed\lpc_revised
echo.
set "SCANROOT="
set /p "SCANROOT=Asset folder: "
if "%SCANROOT%"=="" goto :MENU
echo.
set "OUT="
set /p "OUT=Output JSON [artifacts\asset-intake\asset-catalog.json]: "
if "%OUT%"=="" set "OUT=artifacts\asset-intake\asset-catalog.json"
call :RUN_PCC scan "%SCANROOT%" --output "%OUT%"
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
  echo [PASS] Catalog created:
  echo   %ROOT%\%OUT%
) else (
  echo [FAIL] Scan exited with code %RC%.
)
call :WAIT
goto :MENU

:ANALYZE
cls
echo ========================================================================
echo  PCC SPRITE-SHEET ANALYZER
echo ========================================================================
echo Enter a PNG sprite-sheet path.
echo Example:
echo   assets\source\licensed\lpc_revised\Terrain\cliff_summer.png
echo.
set "SHEET="
set /p "SHEET=PNG sheet: "
if "%SHEET%"=="" goto :MENU
echo.
set "OUT="
set /p "OUT=Output JSON [artifacts\asset-intake\sheet-analysis.json]: "
if "%OUT%"=="" set "OUT=artifacts\asset-intake\sheet-analysis.json"
call :RUN_PCC analyze-sheet "%SHEET%" --output "%OUT%"
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
  echo [PASS] Sheet analysis created:
  echo   %ROOT%\%OUT%
) else (
  echo [FAIL] Sheet analysis exited with code %RC%.
)
call :WAIT
goto :MENU

:TILED
cls
echo ========================================================================
echo  PCC TILED METADATA INSPECTOR
echo ========================================================================
set "TILEDPATH="
set /p "TILEDPATH=TSX/TMX path: "
if "%TILEDPATH%"=="" goto :MENU
echo.
set "OUT="
set /p "OUT=Output JSON [artifacts\asset-intake\tiled-metadata.json]: "
if "%OUT%"=="" set "OUT=artifacts\asset-intake\tiled-metadata.json"
call :RUN_PCC inspect-tiled "%TILEDPATH%" --output "%OUT%"
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
  echo [PASS] Tiled evidence created:
  echo   %ROOT%\%OUT%
) else (
  echo [FAIL] Tiled inspection exited with code %RC%.
)
call :WAIT
goto :MENU

:PREFABS
cls
echo ========================================================================
echo  PCC MULTI-TILE PREFAB EXTRACTION
echo ========================================================================
set "CATALOG="
set /p "CATALOG=Catalog JSON: "
if "%CATALOG%"=="" goto :MENU
echo.
set "OUT="
set /p "OUT=Output JSON [artifacts\asset-intake\prefab-candidates.json]: "
if "%OUT%"=="" set "OUT=artifacts\asset-intake\prefab-candidates.json"
call :RUN_PCC extract-prefabs "%CATALOG%" --output "%OUT%"
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
  echo [PASS] Prefab candidates created:
  echo   %ROOT%\%OUT%
) else (
  echo [FAIL] Prefab extraction exited with code %RC%.
)
call :WAIT
goto :MENU

:HOUSE
cls
echo ========================================================================
echo  PCC SEMANTIC HOUSE PREFAB GENERATOR
echo ========================================================================
set "WIDTH="
set /p "WIDTH=Width in cells [7]: "
if "%WIDTH%"=="" set "WIDTH=7"
set "HEIGHT="
set /p "HEIGHT=Height in cells [7]: "
if "%HEIGHT%"=="" set "HEIGHT=7"
set "ROLEMAP="
set /p "ROLEMAP=Optional role-map JSON [leave blank for unresolved-safe recipe]: "
set "OUT="
set /p "OUT=Output JSON [artifacts\asset-intake\generated-house.prefab.json]: "
if "%OUT%"=="" set "OUT=artifacts\asset-intake\generated-house.prefab.json"

if "%ROLEMAP%"=="" (
  call :RUN_PCC generate-house --width %WIDTH% --height %HEIGHT% --output "%OUT%"
) else (
  call :RUN_PCC generate-house --width %WIDTH% --height %HEIGHT% --role-map "%ROLEMAP%" --output "%OUT%"
)
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
  echo [PASS] House prefab recipe created:
  echo   %ROOT%\%OUT%
  echo.
  echo Note: unresolved roles remain explicit until certified source assets are mapped.
) else (
  echo [FAIL] House prefab generation exited with code %RC%.
)
call :WAIT
goto :MENU

:VALIDATE
cls
echo ========================================================================
echo  PCC ASSET CATALOG VALIDATION
echo ========================================================================
set "CATALOG="
set /p "CATALOG=Catalog JSON: "
if "%CATALOG%"=="" goto :MENU
set "OUT="
set /p "OUT=Output JSON [artifacts\asset-intake\catalog-validation.json]: "
if "%OUT%"=="" set "OUT=artifacts\asset-intake\catalog-validation.json"
call :RUN_PCC validate-catalog "%CATALOG%" --output "%OUT%"
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
  echo [PASS] Catalog validation passed.
) else (
  echo [FAIL] Catalog validation exited with code %RC%.
)
echo   %ROOT%\%OUT%
call :WAIT
goto :MENU

:HELP
cls
echo ========================================================================
echo  PCC ASSET CLI HELP
echo ========================================================================
call :RUN_PCC --help
echo.
echo Scripted calls continue to work normally.
echo Example:
echo   Run-PccAssetTool.cmd inventory-tools . --output artifacts\asset-intake\legacy-tool-inventory.json
call :WAIT
goto :MENU

:RUN_PCC
pushd "%ROOT%" >nul
where py >nul 2>nul
if %ERRORLEVEL%==0 (
  py -3 -m tools.automation.assets.pcc_assets %*
) else (
  python -m tools.automation.assets.pcc_assets %*
)
set "PCC_RC=%ERRORLEVEL%"
popd >nul
exit /b %PCC_RC%

:WAIT
echo.
pause
exit /b 0
