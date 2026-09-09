@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
echo ========================================================================
echo  HAVENWILD ELIZAWY CLIFF SOURCE-02R2 MULTI-CELL EVIDENCE
echo ========================================================================
echo.
where py >nul 2>nul
if %ERRORLEVEL%==0 (
    py -3 "%SCRIPT_DIR%Build-ElizaWyCliffAssemblyEvidenceV2.py" --strict-pinned-hashes
) else (
    python "%SCRIPT_DIR%Build-ElizaWyCliffAssemblyEvidenceV2.py" --strict-pinned-hashes
)
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
    echo [PASS] SOURCE-02R2 multi-cell evidence completed.
    echo.
    echo Outputs:
    echo   artifacts\audits\elizawy_cliff_source02r2\
) else (
    echo [FAIL] SOURCE-02R2 exited with code %RC%.
)
echo.
pause
exit /b %RC%
