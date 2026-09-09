@echo off
setlocal EnableExtensions EnableDelayedExpansion
set "ASSET_DIR=%~dp0"
for %%I in ("%ASSET_DIR%\..\..\..") do set "ROOT=%%~fI"

if not "%~1"=="" (
  call :RUN_PCC %*
  exit /b %ERRORLEVEL%
)

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
echo   3. Build normalization plan from inventory
echo   4. Show canonical asset service registry
echo   5. Intake/source manifest for folder, file, or ZIP
echo   6. SMART scan asset folder ^(recommended^)
echo   7. Specialized / FULL scan asset folder
echo   8. Analyze one PNG sprite sheet
echo   9. Inspect Tiled TSX/TMX metadata
echo  10. Build multi-tile prefab library
echo  11. Generate semantic house prefab recipe
echo  12. Build certification review queue
echo  13. Build derived-output plan
echo  14. Build runtime promotion plan
echo  15. Validate an asset catalog
echo  16. Show CLI help
echo   0. Exit
echo ------------------------------------------------------------------------
set "CHOICE="
set /p "CHOICE=Select an option: "

if "%CHOICE%"=="1" goto :SELFTEST
if "%CHOICE%"=="2" goto :INVENTORY
if "%CHOICE%"=="3" goto :NORMALIZE
if "%CHOICE%"=="4" goto :SERVICES
if "%CHOICE%"=="5" goto :SOURCE
if "%CHOICE%"=="6" goto :SMARTSCAN
if "%CHOICE%"=="7" goto :PROFILESCAN
if "%CHOICE%"=="8" goto :ANALYZE
if "%CHOICE%"=="9" goto :TILED
if "%CHOICE%"=="10" goto :PREFABS
if "%CHOICE%"=="11" goto :HOUSE
if "%CHOICE%"=="12" goto :CERTIFY
if "%CHOICE%"=="13" goto :DERIVE
if "%CHOICE%"=="14" goto :PROMOTE
if "%CHOICE%"=="15" goto :VALIDATE
if "%CHOICE%"=="16" goto :HELP
if "%CHOICE%"=="0" exit /b 0
echo.
echo Invalid selection.
call :WAIT
goto :MENU

:SELFTEST
call :RUN_PCC self-test --output "%TEMP%\pcc-assets-selftest.json"
if exist "%TEMP%\pcc-assets-selftest.json" type "%TEMP%\pcc-assets-selftest.json"
call :WAIT
goto :MENU

:INVENTORY
set "OUT=%ROOT%\artifacts\asset-intake\legacy-tool-inventory.json"
call :RUN_PCC inventory-tools "%ROOT%" --output "%OUT%"
echo.
echo Output: %OUT%
call :WAIT
goto :MENU

:NORMALIZE
set "IN=%ROOT%\artifacts\asset-intake\legacy-tool-inventory.json"
if not exist "%IN%" (
  echo Inventory missing. Running inventory first...
  call :RUN_PCC inventory-tools "%ROOT%" --output "%IN%"
  if errorlevel 1 goto :ACTIONFAIL
)
set "OUT=%ROOT%\artifacts\asset-intake\normalization-plan.json"
call :RUN_PCC normalization-plan "%IN%" --output "%OUT%"
echo.
echo Output: %OUT%
call :WAIT
goto :MENU

:SERVICES
set "OUT=%ROOT%\artifacts\asset-intake\service-registry.json"
call :RUN_PCC services --output "%OUT%"
type "%OUT%"
call :WAIT
goto :MENU

:SOURCE
set "SRC="
set /p "SRC=Source folder/file/ZIP: "
if "%SRC%"=="" goto :MENU
set "OUT=%ROOT%\artifacts\asset-intake\source-manifest.json"
call :RUN_PCC source-manifest "%SRC%" --output "%OUT%"
echo.
echo Output: %OUT%
call :WAIT
goto :MENU

:SMARTSCAN
cls
echo ========================================================================
echo  PCC SMART ASSET LIBRARY SCAN
echo ========================================================================
echo  Stages: inventory - classify - hash/dedupe - metadata - smart deep scan
echo  Results are cached in SQLite and automatically reused on later scans.
echo ------------------------------------------------------------------------
set "SCANROOT="
set /p "SCANROOT=Asset folder [assets\source\licensed\lpc_revised]: "
if "%SCANROOT%"=="" set "SCANROOT=assets\source\licensed\lpc_revised"
set "OUT=%ROOT%\artifacts\asset-intake\asset-catalog.json"
call :RUN_PCC scan "%SCANROOT%" --profile smart --output "%OUT%"
echo.
echo Output: %OUT%
call :WAIT
goto :MENU

:PROFILESCAN
cls
echo ========================================================================
echo  PCC SPECIALIZED ASSET LIBRARY SCAN
echo ========================================================================
echo  Profiles:
echo    index       inventory/hash/classify only
echo    terrain     deep terrain sheets only
echo    structures  buildings/structures/props
echo    characters  one representative per character variant family
echo    props        prop sheets
echo    animations   animation/character representatives
echo    full         every unique grid-compatible non-reference PNG
echo.
set "SCANROOT="
set /p "SCANROOT=Asset folder: "
if "%SCANROOT%"=="" goto :MENU
set "PROFILE="
set /p "PROFILE=Profile [index]: "
if "%PROFILE%"=="" set "PROFILE=index"
set "OUT=%ROOT%\artifacts\asset-intake\asset-catalog-%PROFILE%.json"
call :RUN_PCC scan "%SCANROOT%" --profile "%PROFILE%" --output "%OUT%"
echo.
echo Output: %OUT%
call :WAIT
goto :MENU

:ANALYZE
set "SHEET="
set /p "SHEET=PNG sheet: "
if "%SHEET%"=="" goto :MENU
set "OUT=%ROOT%\artifacts\asset-intake\sheet-analysis.json"
call :RUN_PCC analyze-sheet "%SHEET%" --output "%OUT%"
echo.
echo Output: %OUT%
call :WAIT
goto :MENU

:TILED
set "TILEDPATH="
set /p "TILEDPATH=TSX/TMX path: "
if "%TILEDPATH%"=="" goto :MENU
set "OUT=%ROOT%\artifacts\asset-intake\tiled-metadata.json"
call :RUN_PCC inspect-tiled "%TILEDPATH%" --output "%OUT%"
echo.
echo Output: %OUT%
call :WAIT
goto :MENU

:PREFABS
set "CATALOG=%ROOT%\artifacts\asset-intake\asset-catalog.json"
set /p "CATALOG=Catalog JSON [%CATALOG%]: "
if "%CATALOG%"=="" set "CATALOG=%ROOT%\artifacts\asset-intake\asset-catalog.json"
set "OUT=%ROOT%\artifacts\asset-intake\prefab-library.json"
call :RUN_PCC prefab-library "%CATALOG%" --output "%OUT%"
echo.
echo Output: %OUT%
call :WAIT
goto :MENU

:HOUSE
set "WIDTH="
set /p "WIDTH=Width in cells [7]: "
if "%WIDTH%"=="" set "WIDTH=7"
set "HEIGHT="
set /p "HEIGHT=Height in cells [8]: "
if "%HEIGHT%"=="" set "HEIGHT=8"
set "OUT=%ROOT%\artifacts\asset-intake\generated-house.prefab.json"
call :RUN_PCC generate-house --width %WIDTH% --height %HEIGHT% --output "%OUT%"
echo.
echo Output: %OUT%
call :WAIT
goto :MENU

:CERTIFY
set "CATALOG=%ROOT%\artifacts\asset-intake\asset-catalog.json"
set /p "CATALOG=Catalog JSON [%CATALOG%]: "
if "%CATALOG%"=="" set "CATALOG=%ROOT%\artifacts\asset-intake\asset-catalog.json"
set "OUT=%ROOT%\artifacts\asset-intake\certification-queue.json"
call :RUN_PCC certification-queue "%CATALOG%" --output "%OUT%"
echo.
echo Output: %OUT%
call :WAIT
goto :MENU

:DERIVE
set "CATALOG=%ROOT%\artifacts\asset-intake\asset-catalog.json"
set /p "CATALOG=Catalog JSON [%CATALOG%]: "
if "%CATALOG%"=="" set "CATALOG=%ROOT%\artifacts\asset-intake\asset-catalog.json"
set "OUT=%ROOT%\artifacts\asset-intake\derive-plan.json"
call :RUN_PCC derive-plan "%CATALOG%" --output "%OUT%"
echo.
echo Output: %OUT%
call :WAIT
goto :MENU

:PROMOTE
set "CATALOG=%ROOT%\artifacts\asset-intake\asset-catalog.json"
set /p "CATALOG=Catalog JSON [%CATALOG%]: "
if "%CATALOG%"=="" set "CATALOG=%ROOT%\artifacts\asset-intake\asset-catalog.json"
set "OUT=%ROOT%\artifacts\asset-intake\promotion-plan.json"
call :RUN_PCC promotion-plan "%CATALOG%" --output "%OUT%"
echo.
echo Output: %OUT%
call :WAIT
goto :MENU

:VALIDATE
set "CATALOG=%ROOT%\artifacts\asset-intake\asset-catalog.json"
set /p "CATALOG=Catalog JSON [%CATALOG%]: "
if "%CATALOG%"=="" set "CATALOG=%ROOT%\artifacts\asset-intake\asset-catalog.json"
set "OUT=%ROOT%\artifacts\asset-intake\catalog-validation.json"
call :RUN_PCC validate-catalog "%CATALOG%" --output "%OUT%"
echo.
echo Output: %OUT%
call :WAIT
goto :MENU

:HELP
call :RUN_PCC --help
call :WAIT
goto :MENU

:ACTIONFAIL
echo.
echo [FAIL] Asset operation failed.
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
