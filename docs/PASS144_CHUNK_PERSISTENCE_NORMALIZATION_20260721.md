# Pass 144 — Chunk Data and Persistence Normalization

Pass 144 introduces the canonical versioned chunk persistence envelope. Deterministic baseline data is referenced by seed/version/hash; authored overrides, player deltas, and persistent simulation state are isolated; transient render/editor state and network replication state are never authoritative save data.

New saves use client generation version 5 and initialize `world/chunk_manifest.json`. Version 4 saves migrate by creating the manifest and baseline references while retaining `world.tworld` as a compatibility snapshot. Save writes use temporary files plus recovery copies.

Future persistence changes must update `chunk_persistence_contract_v1.json`, add an explicit migration, and register a validator in the central validation manifest.
