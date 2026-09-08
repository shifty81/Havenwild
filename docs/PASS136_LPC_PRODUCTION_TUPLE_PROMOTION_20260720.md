# Pass 136 LPC Production Tuple Promotion

Pass 136 promotes the six highest-priority shoreline and water-depth material pairs into explicit terrain-v7 tuple entries:

- Sand ↔ Deep Water
- Grass ↔ Deep Water
- Deep Water ↔ Shallow Sand Water
- Water ↔ Mudstone/Dirt Shore
- Deep Water ↔ Shallow Dirt Water
- Shallow Sand Water ↔ Shallow Dirt Water

The builder creates all 14 mixed binary corner arrangements per pair, for 84 new exact entries. Generation uses deterministic seam-safe corner masks and appropriate shallow-water intermediary bands. Runtime forced-shore fallback remains active for unpromoted deep-water/land combinations but now yields to these exact Pass 136 pairs.

Validation requires all 84 entries, exact coverage totals of at least 1,018, no missing tuples, stable runtime ownership, and a focused visual regression board.
