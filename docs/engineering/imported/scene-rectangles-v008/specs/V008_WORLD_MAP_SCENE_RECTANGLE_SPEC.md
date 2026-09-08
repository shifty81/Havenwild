# Havenwild — V008 World Map Scene Rectangle Specification

## Purpose

V008 defines how the V007 macro world becomes playable scene spaces.

V007 answers where the mainland, islands, rivers, mountains, biomes, shore profiles, cities, and harbors exist.

V008 answers how that world is divided into playable, editable, streamable scenes.

## Locked world shape

```text
1 main continent / mainland
9 surrounding smaller islands
10 total major landmasses
```

## Scene scale targets

```text
Small test chunk:        64x64 tiles
Standard outdoor scene: 128x128 tiles
Large/special scene:    160x144 or 192x160 tiles
City district:          multiple linked scene rectangles
Mainland region:        many scene rectangles
```

## Player-facing camera

```text
Approx gameplay camera: 30-45 tiles wide
Approx gameplay camera: 18-28 tiles tall
```

Scene composition must be tuned for the gameplay camera, not full-map screenshots.

## Scene rectangle data

A scene rectangle stores:

```text
terrain semantic cells
height/moisture/slope/biome fields
water/river/fishing regions
shore profile fields
collision hints
object/fringe/overhead layers
transition exits
neighbor seam bands
editor validation markers
```
