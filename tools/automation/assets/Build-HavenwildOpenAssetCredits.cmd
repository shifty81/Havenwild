@echo off
setlocal
python "%~dp0release\Build-HavenwildOpenAssetCreditsV167Y.py" %*
exit /b %ERRORLEVEL%
