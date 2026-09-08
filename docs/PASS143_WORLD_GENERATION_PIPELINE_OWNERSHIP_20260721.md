# Pass 143 — World-Generation Pipeline Ownership

Pass 143 defines the permanent authoritative world-generation order and mutation contract.

## Authoritative order

1. World topology
2. Archipelago skeleton
3. Ocean depth bands
4. Macro biomes
5. Geological form
6. Rivers and watersheds
7. Shore normalization
8. Roads, settlements, and authored anchors
9. Local terrain materialization
10. Props and ecology
11. Structures
12. Validate and bake canonical chunk baseline

Every stage has a stable ID, append-only order, unique seed domain, explicit inputs/outputs, owned mutation layers, forbidden mutation targets, preview policy, regeneration scope, persistence interaction, and validator owner.

## Permanent rules

- Undeclared mutation is forbidden.
- Authored overrides and player deltas survive regeneration.
- Preview generation is reversible; authored stages require explicit commit.
- Stage order and IDs are append-only.
- A stage may only mutate layers declared in `mayMutate`.
- Generated baselines never overwrite player deltas.
- New stages must be registered in both the pipeline contract and validation manifest.
