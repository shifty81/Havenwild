# Havenwild Seamless PCG Surface and Marine Water Audit — Pass 167Z77

## Findings

1. `client_worldgen_test_world_enabled()` previously made the certification pack the practical default, bypassing persistent multi-partition saves.
2. PCG generation authored exterior edge transitions even though runtime coordinate streaming was intended to own outdoor traversal.
3. Exterior camera coordinates were scene-local and clamped to `MAP_W × MAP_H`.
4. Runtime terrain composition drew only `world.active()`.
5. Missing PCG partition coordinates selected `surface_x_*` generic generation, which could expose large grass blocks and repeated-looking terrain.
6. Old PCG water was generic shallow water and lacked explicit saltwater semantics.

## Corrections audited

- Persistent save startup is default; certification startup is explicit opt-in.
- PCG exterior transition generation is removed and old transition records are stripped during load.
- Global exterior camera conversion is used for player, character synchronization, screen picking, and rendering.
- Loaded neighboring exterior terrain is composed around the active partition.
- Missing PCG coordinates receive region-qualified ocean partition IDs and all-deep-ocean storage.
- Generic surface chunks are ignored inside an active PCG coordinate namespace.
- PCG coastline generation creates marine shallow/deep semantics.
- Generation-version migration flood-fills only boundary-connected legacy water, preserving enclosed freshwater.
- Water-source gameplay class separates fresh, salt, and brackish water while leaving V7 shape rendering shared.

## Asset policy

No terrain or water pixels were created, recolored, synthesized, or modified. All coastline and depth presentation remains sourced from the certified V7 atlas lane.

## Certification boundary

Static source, JSON, Python, package, and lineage validation can be completed in the packaging environment. Cargo, Clippy, full tests, release build, and live cross-partition inspection require the Windows workstation.
