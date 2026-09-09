@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
echo ========================================================================
echo  HAVENWILD ELIZAWY CLIFF SOURCE-02 EVIDENCE AUDIT
echo ========================================================================
echo.
where py >nul 2>nul
if %ERRORLEVEL%==0 (
    py -3 "%SCRIPT_DIR%Build-ElizaWyCliffDemoRelationshipEvidenceV1.py" --strict-pinned-hashes
) else (
    python "%SCRIPT_DIR%Build-ElizaWyCliffDemoRelationshipEvidenceV1.py" --strict-pinned-hashes
)
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
    echo [PASS] SOURCE-02 evidence audit completed.
    echo.
    echo Outputs:
    echo   artifacts\audits\elizawy_cliff_demo_relationship_evidence_v1.json
    echo   artifacts\audits\HW_CLIFF_SOURCE_02_DEMO_RELATIONSHIP_EVIDENCE.md
    echo   artifacts\audits\elizawy_cliff_source02\
) else (
    echo [FAIL] SOURCE-02 evidence audit exited with code %RC%.
)
echo.
pause
exit /b %RC%
