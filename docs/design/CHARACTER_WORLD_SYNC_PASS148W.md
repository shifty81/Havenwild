# Pass 148W — Character–World Autosave and Synchronization

Pass 148W extends the account-character/world-link split into runtime lifecycle persistence.

## Active local behavior

The selected character-world link is persisted on manual save, a 120-second autosave cadence, scene transitions, developer scene jumps, return to the main menu, and desktop quit. The same state record retains scene, tile position, global reputation, relationships, quest flags, and last-played time.

## Authority contract

`haven_net` now defines a host-authored `CharacterWorldStateEnvelope`. A client replica must reject client-authored envelopes, stale sequences, mismatched world or character identities, and unavailable scenes.

## Honest boundary

The snapshot, validation, host preparation, and client-application paths exist. A live listen-server transport is not yet connected, so the runtime prepares authoritative envelopes but does not claim network packet delivery or remote persistence is complete.
