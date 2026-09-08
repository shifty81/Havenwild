# LPC Path/Ground Promotion - Pass 137

Pass 137 separates `stone_path` from the shoreline-only `pebble_shore` semantic while preserving the LPC Stone_Tan visual source. It then completes exact transitions for stone and mountain paths against grass, dirt, and sand.

- Exact tuples after promotion: **1032**
- Remaining fallback tuples: **504**
- Missing tuples: **0**
- New generated path entries: **56**

| Pair | Exact shapes |
|---|---:|
| `Stone_Path ↔ Grass` | 14 |
| `Stone_Path ↔ Dirt_Brown` | 14 |
| `Stone_Path ↔ Sand` | 14 |
| `Dirt_Roots ↔ Grass` | 14 |
| `Dirt_Roots ↔ Dirt_Brown` | 14 |
| `Dirt_Roots ↔ Sand` | 14 |

- `pebble_shore` remains mapped to `Stone_Tan` and keeps shoreline normalization behavior.
- `stone_path` now maps to runtime material `Stone_Path`, a semantic alias visually sourced from LPC `Stone_Tan`.
- `mountain_path` remains `Dirt_Roots` but now has complete exact ground transitions.

- Preview: `docs\assets\previews\havenwild_lpc_path_ground_promotion_pass137.png`
