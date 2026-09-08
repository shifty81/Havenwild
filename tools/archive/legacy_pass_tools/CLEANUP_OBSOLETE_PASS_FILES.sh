#!/usr/bin/env bash
set -euo pipefail
rm -f \
  crates/haven_game/src/client_character_creation.rs \
  crates/haven_game/src/client_character_creator_ui.rs \
  crates/haven_game/src/client_character_sprite_runtime.rs
printf '%s\n' 'Havenwild Pass 150K obsolete-file cleanup complete.'
