@echo off
setlocal EnableExtensions
for %%I in ("%~dp0..\..\..") do set "ROOT=%%~fI"
where py >nul 2>nul && (py -3 "%ROOT%\tools\automation\assets\Build-PublishedWorldAssetInventoryV1.py" --root "%ROOT%" %* & exit /b %ERRORLEVEL%)
where python >nul 2>nul && (python "%ROOT%\tools\automation\assets\Build-PublishedWorldAssetInventoryV1.py" --root "%ROOT%" %* & exit /b %ERRORLEVEL%)
echo Python 3 was not found.
exit /b 1
