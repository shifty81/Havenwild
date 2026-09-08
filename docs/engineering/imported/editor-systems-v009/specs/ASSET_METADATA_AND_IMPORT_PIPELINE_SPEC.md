# Asset Metadata and Import Pipeline Spec

## Rule

No major asset should be treated as just a raw PNG.

Every major asset needs metadata.

## Asset metadata categories

```text
terrain_material
transition_mask
overlay_decal
water_animation
tile_atlas
character_sheet
object_sprite
wall_autotile
furniture
item_icon
ui_skin
animation_sheet
scene_template
```

## Required fields

```text
asset_id
schema_version
source_file
runtime_file
cell_size
grid_size
tags
authoring_tool
license_status
originality_status
import_time
last_validated
validation_state
```

## Optional fields

```text
collision masks
interaction sockets
animation frames
autotile rules
anchor points
preview rules
palette
layer rules
hot reload behavior
runtime cache path
```

## Import pipeline

```text
select file
detect type
create metadata
validate dimensions
generate preview
register asset
create runtime cache
show import report
```

## Validation examples

```text
PNG dimensions not divisible by cell size
missing metadata
wrong animation frame count
collision mask missing
anchor missing
palette drift
duplicate asset id
unlicensed/reference-only source
```
