@echo off
setlocal
for %%F in (
  "crates\haven_game\src\client_character_creation.rs"
  "crates\haven_game\src\client_character_creator_ui.rs"
  "crates\haven_game\src\client_character_sprite_runtime.rs"
) do (
  if exist "%%~F" del /f /q "%%~F"
)
echo Havenwild Pass 150K obsolete-file cleanup complete.
