# Pass 138 — Character Client Integration and Persistent Profiles

## Locked flow
New Game and Load first resolve a persistent character profile. Up to five profiles exist independently from unlimited world saves and multiplayer servers.

## Added
- Account-level character profile index and per-profile JSON persistence.
- Five-profile hard limit and active-profile selection.
- World saves reference `selected_character_profile_id`; they do not own character identity.
- Client character-creation state with appearance, colors, ordinary starter clothing, review and commit validation.
- Deterministic layered preview recipe with neutral four-direction idle aliases.

## Ownership boundary
Profile-owned: identity, appearance, colors, portable progression and permitted equipment.
World-owned: position, world spawn, relationships, quests, property and businesses.

## Deferred
Actual macroquad creator widgets, texture loading and final composed sprite draw calls are the next GUI/runtime pass.
