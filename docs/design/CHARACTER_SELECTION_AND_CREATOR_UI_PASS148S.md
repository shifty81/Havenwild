# Pass 148S — Character Selection and Creator UI

Havenwild separates persistent characters from unlimited world saves. Both New Game and Load Game choose a character before browsing worlds.

## UI model

The frontend exposes five character profile cards. Occupied cards can be selected, edited, or deleted. Empty cards open the modular LPC creator. Character cards use the same layered appearance record as the player runtime, NPC generation, portraits, equipment rendering, and multiplayer replication.

The world browser is dynamic and unbounded. Legacy three-slot saves remain importable but are not the forward UI limit.

## Current integration boundary

`CharacterSelectionUiModel` is the native frontend state/model layer. The existing macroquad three-card screen remains a compatibility frontend until its rendering and input code is replaced by this model. No claim is made that the visual replacement is complete before the Windows runtime build and screenshot verification.
