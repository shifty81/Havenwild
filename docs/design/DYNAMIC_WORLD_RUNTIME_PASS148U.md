# Pass 148U — Dynamic World Runtime Migration

Havenwild runtime launch now carries a persistent `CharacterId` and dynamic `WorldSaveId` rather than a fixed `ClientSaveSlot`.

## Runtime ownership

- Character profiles remain account-owned and capped at five.
- World directories are dynamically named `world_<stable-id>` and are unlimited.
- Each world stores `world.json`, `world.tworld`, generated content, chunks, paint deltas, previews, and per-character link files.
- Launch requests contain both the selected character and selected world.

## Legacy migration

The three historical `slot_1` through `slot_3` directories are migrated to `world_legacy_slot_1` through `world_legacy_slot_3`. Existing world files are preserved and their `slot.json` metadata is translated to `world.json`.

## Remaining work

The selected character identity is retained by `Game`; subsequent passes should restore and update the character-world link position, scene, relationships, inventory policy, and multiplayer session state during runtime save/load.
