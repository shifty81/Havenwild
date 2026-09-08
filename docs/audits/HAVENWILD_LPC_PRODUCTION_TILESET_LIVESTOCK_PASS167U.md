# Havenwild Pass 167U — LPC Production Tileset and Livestock Promotion

## Purpose

Continue the LPC asset and tileset lane with production-ready source geometry,
data-owned gameplay contracts, editor source bindings, and test-world gallery
ownership. Generated atlases remain derived outputs and are never treated as
editable world truth.

## Promoted livestock source set

The complete locally reviewed LPC farm-animal source set is now present:

- chicken: walk, eat, shadow;
- cow: walk, eat, shadow;
- llama: walk, eat, shadow;
- pig: walk, eat;
- sheep: walk, eat.

The source submission is credited to Daniel Eddeland (daneeklu), with Havenwild
selecting CC-BY 3.0. Each visual sheet is indexed as four directions by four
frames. Direction rows are north, west, south, and east. The runtime catalog
stores exact frame rectangles, alpha bounds, bottom-center foot anchors, sheet
hashes, and collision-ownership rules.

## Livestock gameplay definitions

Added data-driven species definitions for chicken, cow, llama, pig, and sheep.
The data owns needs, housing, feed, movement, produce, secondary outputs,
breeding, behavior, and animation aliases. Art does not determine simulation
values or collision.

## Tileset normalization

The LPC terrain-v7 TSX is now represented in a compact production visual
registry containing:

- 34 semantic terrain material sources;
- exact pure-fill source rectangles;
- 2,048-tile source-sheet metadata;
- four structural cliff material sheets;
- animated-water and waterfall source geometry;
- explicit semantic-versus-visual ownership rules.

Structural cliffs remain selected from elevation/cliff topology. Waterfalls
remain selected from Hydrology V2 plus structural waterfall queries.

## World-to-Pixel Studio coverage

A v0.2 source-binding registry exposes 49 reviewed source bindings covering:

- terrain-v7 semantic material fills;
- grass, dark-dirt, sand, and snow cliff sheets;
- animated waterfall source art;
- all promoted livestock walk/eat sheets.

Third-party source normalization still uses Havenwild-owned overrides. Large
atlas rebuilds remain background jobs.

## Client-loaded test-world galleries

The editor test world now has a formal gallery contract for:

- terrain materials and transitions;
- structural cliffs, ramps, water-facing faces, and cave hosts;
- shallow/deep water, flow, waterfalls, and freeze/thaw;
- livestock idle, walking directions, and eating;
- future crop, tree, plant, farm-building, and fish rows.

The client worldgen test mode remains the target presentation world. Gallery
content cannot mutate player saves.

## Deferred archive promotion

Crops, fruit trees, deciduous trees, conifers, plants, farm buildings, and fish
remain in the approved acquisition queue. They are not marked production-ready
until their downloaded archives and bundled credit files are inspected locally,
deduplicated against the pinned LPC repository, and mapped at exact frame or
cell level.

## Validation

Pass 167U validates:

- five livestock species and matching gameplay definitions;
- exact image dimensions and 16-frame walk/eat mappings;
- terrain-v7 source geometry and material count;
- unique world asset source-binding IDs;
- editor test-world gallery ownership;
- source-file presence.
