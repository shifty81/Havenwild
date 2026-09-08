@echo off
setlocal
cd /d "%~dp0\.."

echo [Havenwild] Mounting the complete Universal LPC character repository...
python tools/automation/characters\Ensure-UniversalLpcGenerator.py || exit /b %errorlevel%

echo [Havenwild] Indexing all character, clothing, animation, tool, weapon, and shield sources...
python tools/automation/characters\Build-UniversalLpcCompleteRepositoryIndexV167Z7.py || exit /b %errorlevel%

python tools/automation/characters\Build-UniversalLpcCharacterAuthorityV167W.py || exit /b %errorlevel%
python tools/automation/characters\Build-UniversalLpcUsageManifestV167X.py || exit /b %errorlevel%
python tools/automation/characters\Build-UniversalLpcGameplayWardrobeV167Y6.py || exit /b %errorlevel%

echo Universal LPC complete repository authority is ready.
echo Source mount: assets\source\licensed\universal_lpc_generator
endlocal
