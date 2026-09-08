# Pass 148V — Character–World Runtime State

The selected persistent character now restores world-local state from its `CharacterWorldLink` when a dynamic world launches. The runtime restores the active scene, tile position, and world reputation while preserving relationship and quest-flag maps for later gameplay integration.

Manual world saves update the same link atomically. Frontend launch no longer replaces an existing link with a new blank record; it loads and touches the existing record. Invalid or missing scenes fall back to the active world spawn and emit a diagnostic.

Future autosave, disconnect, and scene-transition hooks should call `persist_character_world_state` through the same pathway.
