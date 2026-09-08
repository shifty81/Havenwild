# Havenwild LPC Expandable Pond Families Pass 87

Date: 2026-07-12

## Result

Pass 87 promotes the pond and basin structures in the locked `ElizaWy/LPC`
`Terrain/terrain_summer.png` source as expandable terrain families rather than fixed
3x3 pictures or unrelated atlas cells.

The reviewed LPC terrain layout uses:

- one authored **3x3 outer block** containing outer corners, cardinal edges, and a
  repeatable center;
- one authored **2x2 inner-corner block** containing concave corners for future
  freeform/blob boundaries;
- an explicit repeatable base-fill cell when the authored family is an overlay.

This is now preserved as data instead of guessed from atlas index order.

## Locked LPC foundation

Added:

- `content/assets/intake/lpc_source_lock_v0_1.json`
- `content/assets/intake/lpc_expandable_terrain_families_v0_1.json`

The current source lock pins:

- Repository: `ElizaWy/LPC`
- Commit: `f07f7f5892e67c932c68f70bb04472f2c64e46bc`
- Source: `Terrain/terrain_summer.png`
- Project copy: `assets/source/licensed/lpc_revised/terrain/terrain_summer.png`
- Size: 512x832
- SHA-256: `1251a6ea556330190ccb1e3af166eb69fbec4b7a3f7d51c1f54728abd75bd752`

Builds validate the locked source before promoting any pond definitions. A future LPC
update must be an explicit source-lock revision rather than silently shifting source
coordinates.

## Mapped expandable families

Fourteen authored LPC families are now mapped:

- grass-bank pond A
- grass-bank pond A overlay
- dirt-bank pond A
- dirt-bank pond A overlay
- grass-bank pond B
- grass-bank pond B overlay
- dirt-bank pond B
- dirt-bank pond B overlay
- sand-bank pond
- pond foam overlay
- pale-shore pond overlay
- deep-water basin
- depth-ring overlay A
- depth-ring overlay B

Overlay families receive an explicit base water/depth fill before the authored LPC
edge tile is composited. This prevents transparent centers from appearing as black or
empty holes.

Generated runtime/editor manifest:

`assets/generated/worldgen_v0_1/terrain/lpc_expandable_ponds_32.json`

## Runtime and native-editor rendering

`StampRegistry` now supports `ExpandableStampDefinition` with:

- base-fill tile
- 3x3 outer tile roles
- 2x2 inner-corner tile roles
- minimum width and height
- freeform capability metadata

For rectangular placement, runtime and editor render each 32x32 source cell at native
pixel scale:

```text
NW corner | north edge repeated | NE corner
west edge | center repeated     | east edge
SW corner | south edge repeated | SE corner
```

No pond image is stretched. Enlarging a pond repeats its edge and center cells.

## Editor resizing

When an expandable pond stamp is selected in the native editor Inspector, it now
shows:

- Width -
- Width +
- Height -
- Height +
- Reset 3x3 Source Size

Resizing updates:

- visual footprint
- collision footprint
- interaction footprint
- bottom-center anchor offsets

The update is recorded as an undoable transaction. The resized footprint is already
stored by the existing `world.tworld` stamp record, so it survives Save/Save All and
reload without a save-format break.

## Preview

`docs/assets/previews/havenwild_lpc_expandable_ponds_pass87.png`

The preview renders every mapped family at 3x3, 5x4, and 8x6. It is generated from
the same locked source coordinates used by runtime/editor data.

## Build commands

From the repository root:

```bat
tools/build/Build.cmd tiles
tools/build/Build.cmd apps
```

On Bash:

```bash
./tools/build/Build.sh tiles
./tools/build/Build.sh apps
```

The tile pipeline now runs:

1. production terrain generation
2. production environment generation
3. corrected LPC coastline promotion
4. expandable LPC pond promotion
5. multi-tile stamp preview generation

## Validation

Completed in this environment:

- Python syntax compilation
- locked-source hash and dimension validation
- deterministic pond manifest and preview generation
- 216 JSON content files parsed
- architecture validation across 177 Rust files
- open-world preset validation
- editor validators through V86
- existing terrain/coastline/save regeneration validators
- new expandable pond validator

New validator:

`tools/automation/validation/checks/terrain/Validate-LpcExpandablePondFamiliesV86.py`

Rust compilation, rustfmt, Clippy, and Rust unit tests were not run because this
environment does not contain a Rust toolchain. Run `tools/build/Build.cmd all` on the Windows
development machine before promoting the pass.

## Deliberate boundary of this pass

Rectangular expansion is active now.

The 2x2 inner-corner cells are fully mapped and validated, but arbitrary freeform/blob
footprints are not yet stored or edited by placed stamp instances. The next pond pass
should add:

- semantic occupied-cell footprints
- paint/grow/shrink pond boundary editing
- 8-neighbor outer/inner-corner resolution
- islands and holes
- PCG pond generation from the same family contract
- context-menu commands for resize, edit boundary, change family, and regenerate

This pass establishes the correct LPC source contract and prevents the next freeform
resolver from being built on guessed atlas indexing.
