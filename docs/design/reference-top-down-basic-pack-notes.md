# Pixel Art Top Down Basic Reference Notes

Source archive inspected:

```text
C:/Users/Shifty/Downloads/Pixel Art Top Down - Basic v1.2.3.zip
```

Local reference extraction:

```text
assets/raw/reference-packs/pixel-art-top-down-basic-v1.2.3/extracted
```

Documentation shortcut in the archive points to:

```text
https://docs.cainos.net/pixel-art-top-down-basic
```

## Useful Lessons

- The overview image uses a large region-like composition with raised platforms, stair links, wall edges, prop landmarks, path loops, and small readable nodes.
- Props stay small relative to the full scene. This reinforces the Havenwild scale rule: buildings and farms should not consume the whole island preview.
- Stone paths are broken and varied, which is a better model for world readability than solid rectangular road bands.
- Structures work as boundaries, terraces, gates, stairs, and occluders. These are useful examples for the 2.5D presentation layer.
- Plant and prop sheets include shadow variants, which supports the existing direction of separate shadow/overlay layers.

## Project Usage Guidance

- Treat this pack as reference and example material unless its license is explicitly cleared for redistribution inside the project.
- Use it to guide composition, scale, path language, stairs, walls, terraces, and prop density.
- Do not copy its sprites into `assets/generated` as project-owned art without a license note.
- For editor previews, prefer deriving our own island graph and scene render data, using this pack only as visual inspiration.

## Asset Categories Observed

| File | Size | Notes |
|---|---:|---|
| `Scene Overview.png` | 1200x1200 | Strong reference for region composition and path/terrace layout. |
| `TX Tileset Grass.png` | 256x256 | Grass and broken stone-path examples. |
| `TX Tileset Stone Ground.png` | 256x256 | Stone ground/path variants. |
| `TX Tileset Wall.png` | 512x512 | Wall/edge presentation examples. |
| `TX Struct.png` | 512x512 | Stairs, wall segments, gates, structural edges. |
| `TX Props.png` | 512x512 | Props, signs, crates, graves, fountain, rocks. |
| `TX Plant.png` | 512x512 | Trees/plants for object density reference. |
| `TX Shadow.png` / `TX Shadow Plant.png` | 512x512 | Separate shadow layer references. |
