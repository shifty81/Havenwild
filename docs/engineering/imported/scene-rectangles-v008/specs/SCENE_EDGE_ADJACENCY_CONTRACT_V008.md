# Scene Edge and Adjacency Contract V008

## Problem

If scenes are generated separately, rivers, roads, beaches, cliffs, paths, and biome transitions can break at scene edges.

## Rule

Every scene rectangle has two edge bands:

```text
4-tile seam validation band
8-tile decoration-safe band
```

## 4-tile seam validation band

Used for:

```text
water depth continuity
river continuation
shore profile continuity
road/path continuation
cliff/ledge continuation
biome blend continuity
collision/water/fishing region continuity
```

## 8-tile decoration-safe band

Prevents large objects from breaking scene edges.

Later applies to:

```text
trees
buildings
cliff props
large rocks
bridges
fences
city structures
```

Large objects can cross a scene edge only if explicitly seam-locked.

## Neighbor stitch signatures

Each scene exports:

```text
north/east/south/west edge signatures
corner signatures
river exit points
road exit points
shoreline exit points
height samples
biome samples
shore profile samples
```
