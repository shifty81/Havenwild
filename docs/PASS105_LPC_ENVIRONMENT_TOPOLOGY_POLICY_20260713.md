# Havenwild Pass 105 - LPC Environment Topology Policy

Pass 105 continues from the Pass 104 placement hotfix.

## Purpose

The broader design direction is correct: environment tiles should not be a pile
of unrelated special cases. Grass, sand, roads, caves, floors, walls, bridges,
cliffs, and modular building pieces should all follow a shared topology model.

Pass 105 adds that contract without changing tile rendering behavior.

## Added

- `content/assets/lpc/lpc_environment_topology_policy_v0_1.json`
- V117 standalone validation for the policy/source contract.

## Policy Buckets

- `semantic_boundary_replacement`: grass, dirt, sand, wet sand, pebble shore,
  water, shallow/deep water, ocean/river aliases, and mud banks.
- `same_family_assembly`: roads, paths, bridges, floors, walls, cliffs, cave
  floors, and cave walls.
- `derived_overlay_or_state`: tilled/watered soil, crops, greenhouse zones,
  river mouths, and shore foam.
- `non_tileable_object_or_stamp`: tall grass and future prop-like vegetation.

## Safety

This pass does not reintroduce Pass 103's broken mixed-role layering. V116 still
requires one complete replacement role per cell unless a future source family
has authored mixed-role cells for that exact topology.

## Next Art Pass

The next practical LPC art promotion should start with roads/paths as a
same-family assembly set, then caves/interiors/structures once their source
families are mapped.
