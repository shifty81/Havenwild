# Pass 163E Terrain Source Duplication and Generator Audit

## Finding

The newly uploaded `terrain-v7.png` is byte-identical to the project copy.

- SHA-256: `d098d23fbe6bb51b53f5d719d05a8e620d393f9d831bb14d2ed201b650163b7b`
- Dimensions: 1024x2048

The project already contained the complete generated terrain map:

- Path: `content/assets/lpc/source/lpc-terrains-v7/terrain-map-v7.png`
- Dimensions: 512x31488
- SHA-256: `adc395adc3defb182389d4ca888afdd896bdd6b672ab92609b428a5bbd79cd25`

The 33x2048 reference duplicate was damaged and has been removed.

## Generator capability

`tools/automation/terrain/Build-LpcMappedTerrainV7.py` already consumes the complete generated map and source variant sheet. It now regenerates:

- `assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.png`
- `assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.json`
- `docs/audits/generated/havenwild_terrain_standard_v1_runtime_atlas_preview.png`

The generated runtime manifest contains exact tuple mappings and authored pure-fill variants. No speculative pixel reconstruction was required.
