# Havenwild Cliff Source Authority Decision V1

## Locked rule

**Original ElizaWy/LPC source art and demonstrated assemblies are the cliff visual authority.**

Structural topology remains Havenwild-owned gameplay data. It selects a
**certified source-native assembly**; it does not manufacture replacement cliff
art from abstract edge masks.

## KEEP

- `assets/source/licensed/lpc_revised` as immutable pinned source.
- ElizaWy seasonal cliff sheets.
- `_ Test Scenes/DemoGame - 2 - Summer.png`.
- `_ Test Scenes/Test Landscape.png`.
- Existing demo-grounded straight south, SW, SE, cave and ladder source roles.
- Havenwild structural levels, collision and traversal as gameplay authority.
- Existing Tiled TSX importer as the normalization path for donor metadata.

## AUDIT / REWRITE

- `ElizaWyCliffConnectedRecipeRole::SideEntryRampPending`.
- c8 complete transition/side-entry strip.
- right-side terminal adjacency.
- any ridge/corner whose runtime source comes from a companion cliff family.
- resolver mapping from structural topology to source-native assemblies.
- derived runtime overlays so they carry explicit lineage back to original art.

## RETIRE AFTER REPLACEMENT IS CERTIFIED

- companion `LPC_cliffs_grass.png` as ramp/cliff visual authority;
- `lpc_cliff_ramp_provider` runtime visual ownership;
- `oga_cliff_source` if it has no other certified consumer;
- six-cell geometry assumptions that exist only to fit the retired 3x4 ramp.

Nothing above is deleted by HW-CLIFF-SOURCE-01. This pass creates the evidence
needed to remove it safely in a later runtime migration.

## Metadata donor policy

The JaidynReiman 2024 Tiled exterior pack is **relationship evidence**, not art
authority. Its Terrain/Wang metadata, properties, animations and collision can
help recover intended assembly relationships. Havenwild must map those
relationships back to the original pinned ElizaWy source before runtime use.

Donor collision is evidence only. Havenwild's structural collision/traversal
remains authoritative.

## Runtime migration gate

No new cliff/ramp visual patch should be accepted until:

1. original `cliff_summer.png` is present and hashed;
2. Summer demo and Test Landscape are present and hashed;
3. side-entry/c8 relationships are resolved from source/demo/TSX evidence;
4. foreign-family dependencies are enumerated;
5. every replacement recipe has source rect/stamp, anchor, footprint, valid
   neighbors and evidence lineage;
6. a validator can reject cross-family cliff/ramp substitution.

Only after those gates pass should runtime rendering change again.
