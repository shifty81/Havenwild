# Imported Asset Zip Audit - 2026-05-25

## Summary

Two external asset archives were staged into the project under:

```text
assets/raw/reference-packs/
```

The project now has a machine-readable reference manifest at:

```text
content/packs/reference_asset_packs.json
```

## Pixel Art Top Down - Basic

Requested archive:

```text
C:/Users/Shifty/Downloads/Pixel Art Top Down - Basic v1.2.3 (1).zip
```

Available archive used:

```text
C:/Users/Shifty/Downloads/Pixel Art Top Down - Basic v1.2.3.zip
```

Project location:

```text
assets/raw/reference-packs/pixel-art-top-down-basic-v1.2.3/
```

Extracted contents:

| Type | Count | Approx size |
|---|---:|---:|
| `.png` | 12 | 1.18 MB |
| `.unitypackage` | 1 | 1.33 MB |
| `.txt` | 1 | <0.01 MB |
| `.url` | 1 | <0.01 MB |
| `.zip` source archive | 1 | 2.50 MB |

Useful project signals:

- `Scene Overview.png` is a strong reference for island/region composition scale.
- `TX Tileset Grass.png`, `TX Tileset Stone Ground.png`, and `TX Tileset Wall.png` are useful references for path, wall, stair, and edge language.
- `TX Struct.png`, `TX Props.png`, and `TX Plant.png` are useful for object-density and prop-scale planning.
- Separate shadow sheets support the current shadow/overlay layer direction.

License status:

- No license file was found inside the archive.
- The archive includes a documentation shortcut to `https://docs.cainos.net/pixel-art-top-down-basic`.
- Treat as reference-only until license terms are explicitly recorded.

## Universal Animation Library

Requested archive:

```text
C:/Users/Shifty/Downloads/Universal Animation Library[Standard] (4).zip
```

Available archive used:

```text
C:/Users/Shifty/Downloads/Universal Animation Library[Standard] (3).zip
```

Project location:

```text
assets/raw/reference-packs/universal-animation-library-standard/
```

Extracted contents:

| Type | Count | Approx size |
|---|---:|---:|
| `.fbx` | 1 | 23.69 MB |
| `.glb` | 1 | 7.74 MB |
| `.png` | 3 | 0.84 MB |
| `.txt` | 1 | <0.01 MB |
| `.zip` source archive | 1 | 8.33 MB |

License status:

```text
CC0 1.0 Universal (CC0 1.0)
Public Domain Dedication
Models by @Quaternius
```

Useful project signals:

- Use as source/reference for character motion vocabulary.
- Feed a future native animation catalog in the Rust editor.
- Prioritize tavern/farm verbs first: idle, walk, jog, interact, pickup, sitting, talking, push, fixing/kneeling.

## Integration Rules

- Keep raw third-party packs under `assets/raw/reference-packs`.
- Do not place unreviewed third-party art in `assets/generated`.
- Promote assets into runtime registries only after license and intended use are recorded.
- Native Rust editor should read `content/packs/reference_asset_packs.json` for asset review panels.
