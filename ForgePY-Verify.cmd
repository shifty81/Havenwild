@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call "%~dp0ForgePY.cmd" package-verify
if errorlevel 1 exit /b %errorlevel%
call "%~dp0ForgePY.cmd" runtime-self-test
if errorlevel 1 exit /b %errorlevel%
call "%~dp0ForgePY.cmd" doctor
exit /b %errorlevel%
