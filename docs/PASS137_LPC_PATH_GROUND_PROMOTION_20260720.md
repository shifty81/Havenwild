# Pass 137 — LPC Path and Ground Pair Completion

Pass 137 separates the walkable stone-path semantic from the shoreline pebble semantic and completes the production path-to-ground transition families.

## Runtime changes

- `pebble_shore` remains mapped to LPC `Stone_Tan`.
- `stone_path` now maps to runtime-only semantic material `Stone_Path`.
- `Stone_Path` deliberately reuses the LPC `Stone_Tan` fill artwork while owning independent topology and behavior.
- `mountain_path` remains mapped to LPC `Dirt_Roots`.

## Exact topology families

All 14 binary corner arrangements are now exact for:

- Stone Path ↔ Grass
- Stone Path ↔ Dirt
- Stone Path ↔ Sand
- Mountain Path ↔ Grass
- Mountain Path ↔ Dirt
- Mountain Path ↔ Sand

Pass 137 generated 56 missing tuple images. Existing LPC-authored Dirt_Roots transitions supplied the remaining exact shapes.

## Coverage

- Exact: 1,032
- Fallback: 504
- Missing: 0

The semantic split increases the valid material-combination space, so the global net exact increase is intentionally smaller than the number of generated images. This prevents path rendering from inheriting shoreline-only behavior and keeps future normalization rules honest.

## Validation

Passed:

- V133 tuple coverage audit
- V134 tuple promotion plan
- V135 editor terrain and water paint
- V136 production shoreline tuple promotion
- V137 path/ground promotion
- Content JSON validation: 168 files

Rust compilation was not executed because the current container does not include Cargo or rustc.
