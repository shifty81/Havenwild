# LPC Production Tuple Promotion - Pass 136

Pass 136 converts the six highest-frequency production shoreline and water-depth pairs from guarded pure-fill fallback ownership into explicit deterministic terrain-v7 tuple entries.

- Exact tuples after promotion: **1032**
- Remaining fallback tuples: **504**
- Missing tuples: **0**
- New generated exact entries: **84**

| Pair | Exact promoted shapes |
|---|---:|
| `Sand ↔ Water_Deep` | 14 |
| `Grass ↔ Water_Deep` | 14 |
| `Water_Deep ↔ Water_Shallows_Sand` | 14 |
| `Water ↔ Mudstone_Brown` | 14 |
| `Water_Deep ↔ Water_Shallows_Dirt` | 14 |
| `Water_Shallows_Sand ↔ Water_Shallows_Dirt` | 14 |

The generated tiles use seam-safe deterministic corner masks. Water/land pairs use the appropriate shallow-water intermediary band where available, while mixed tiles remain stable across water animation frames.

- Preview: `docs\assets\previews\havenwild_lpc_production_tuple_promotion_pass136.png`
