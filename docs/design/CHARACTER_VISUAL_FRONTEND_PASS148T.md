# Pass 148T — Character Visual Frontend

## Implemented

The Macroquad startup frontend now renders four explicit stages: main menu, five-card persistent character selection, character creation/editing, and world selection. New Game and Load Game both require character selection before world selection.

Characters are stored in the account-level `CharacterProfileStore`. Empty cards create profiles; occupied cards select, edit, or delete profiles. Character deletion intentionally leaves world saves intact.

The preview renderer uses the current generated LPC player source when available and retains the modular `CharacterAppearance` layer count and profile identity. A nonproduction silhouette is shown only when that source is absent. Full per-layer source composition still requires the LPC source inventory/index pass.

The world screen dynamically scans all world directories and reports their count. Runtime launch still uses the three migrated `ClientSaveSlot` roots because `Game`, `ClientSavePaths`, and world generation remain typed around `ClientSaveSlot`. The UI states this boundary instead of claiming unlimited-world runtime launch is complete.

## Next migration

Replace `Game::new(ClientSaveSlot, ...)` and `ClientSavePaths::for_slot` with `WorldSaveId`/dynamic-root launch context, then create worlds directly under unlimited world IDs. After that, index concrete LPC component sheets and compose each enabled appearance layer rather than using the current base source fallback.
