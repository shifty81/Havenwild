# Pass 126D - V128 Water Material Validator Hotfix

This pass updates the V128 water animation validator so it checks for the required
water materials independently instead of requiring one exact Rust match-arm
format.

The previous guard looked for:

```text
LpcMappedTerrainMaterial::Water | LpcMappedTerrainMaterial::WaterDeep
```

That is too brittle because `cargo fmt` or nearby edits can legally split the
match arm across multiple lines while preserving the exact same runtime behavior.
The validator now requires both material names separately:

- `LpcMappedTerrainMaterial::Water`
- `LpcMappedTerrainMaterial::WaterDeep`

This keeps V128 focused on the real contract: pure water and deep water remain
part of the animated water-fill path, while shore/depth mixed edges stay stable.

Validated locally:

- `python -m py_compile tools/automation/validation/checks/characters/Validate-LpcWaterAnimationAndShoreDepthV128.py tools/automation/validation/checks/characters/Validate-LpcWaterAnimationOwnershipV129.py tools/automation/validation/checks/characters/Validate-LpcSparseWaterAnimationV130.py`
- `python tools/automation/validation/checks/characters/Validate-LpcWaterAnimationAndShoreDepthV128.py`
- `python tools/automation/validation/checks/characters/Validate-LpcWaterAnimationOwnershipV129.py`
- `python tools/automation/validation/checks/characters/Validate-LpcSparseWaterAnimationV130.py`
