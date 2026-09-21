@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call "%~dp0ForgePY.cmd" package-verify
if errorlevel 1 exit /b %errorlevel%
call "%~dp0ForgePY.cmd" init
if errorlevel 1 exit /b %errorlevel%
call "%~dp0ForgePY.cmd" doctor
if errorlevel 1 exit /b %errorlevel%
echo.
echo [PASS] ForgePY U5 is installed, repository-scanned, onboarded and verified in this repository.
echo Launch ForgePY-GUI.cmd for the ForgePY graphical interface. Review Build Plan before the first build.
echo Use HavenwildTools.cmd for the authoritative Havenwild PCC or ForgePY.cmd for CLI/Cortex use.
