# Pass 148R — Universal LPC Character Pipeline

## Locked flow
Both New Game and Load enter character selection before world/save selection. Characters are account-level persistent profiles; worlds are independent and unlimited.

## Character ownership
A profile owns identity, modular LPC appearance, progression, equipment, portable inventory, portrait and animation profiles. A world owns terrain, NPC/world state, world position, relationships, reputation, quests and server permissions.

## LPC composition
LPC sheets are indexed as reusable layers rather than one flattened character. Player runtime, NPC generation, the character creator, portrait generation and multiplayer appearance replication consume the same layer catalog.

## Compatibility
The old three-slot save layout remains readable as a migration format. It is no longer the forward save-capacity contract.
