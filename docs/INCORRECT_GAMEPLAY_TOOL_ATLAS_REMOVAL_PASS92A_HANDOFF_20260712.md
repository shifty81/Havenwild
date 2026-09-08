# Incorrect Gameplay Tool Atlas Removal — Pass 92A

## Correction

The provisional gameplay-tool atlas introduced in Pass 92 used LPC source cells that belong to other object/composition roles. Those cells are no longer treated as axe, pickaxe, hoe, watering can, hammer, fishing rod, scythe, or hand icons.

Removed:

- `tools/automation/Build-LpcGameplayToolAtlas.py`
- `assets/generated/lpc/ui/havenwild_gameplay_tools_32.png`
- `assets/generated/lpc/ui/havenwild_gameplay_tools_32.json`
- runtime loading and rendering of that atlas
- build and validation requirements that regenerated it

## Preserved

- the independent player-facing eight-slot gameplay hotbar
- `1–8` gameplay selection
- normal wheel gameplay-tool cycling
- `Alt + wheel` camera zoom
- `Ctrl + 1–0` developer palette selection
- Pass 92 terrain correction
- native-editor camera/material reset
- LPC player, object, terrain, stamp, and world-paint generation

Until proper tool sprites are reviewed and mapped, the HUD uses neutral two-letter text markers. No unrelated LPC source cell is displayed as a gameplay tool.

## Apply

For the overlay patch:

1. Extract it into the Havenwild repository root.
2. Run `Apply-Pass92A.cmd` once to delete the rejected generated files.
3. Run:

```bat
tools/build/Build.cmd lpc-runtime
tools/build/Build.cmd all
```

`lpc-runtime` no longer creates the rejected tool atlas.

## Verification performed in the packaging environment

Passed:

- `python tools/automation/validation/checks/editor/Validate-LpcClientEditorStabilityV102.py`
- Python syntax checks for V102 and the cleanup script
- `bash -n tools/build/Build.sh`
- `bash -n tools/build/dev.sh`

Rust/Cargo was unavailable, so the Windows build remains the authoritative Rust compile, Clippy, and test verification.
