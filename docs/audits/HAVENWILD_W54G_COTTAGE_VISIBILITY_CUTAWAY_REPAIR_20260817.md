# Havenwild W54G — Cottage Visibility + Cutaway Repair

## Screenshot finding

The W54F exterior still showed tall gray/white vertical strips behind the roof. Those were not roof assets: they were `rear_interior_finish` / room-divider wall pieces leaking into exterior presentation because default-level walls were always visible while outside. The thin red/green door line was the `open_left` door state, not a missing door texture.

## Repair

- Exterior presentation now suppresses pieces in `building.wall_interior.*`.
- Rear and divider interior visual runs use the already-published exact cutaway-cap family rather than 1x3 drywall wall-face strips.
- Front and bedroom doors default to `closed`; interaction opens them through the existing persistent BuildingInstance opening-state authority.
- W54F 10x8 footprint, room program, front route alignment, and edge-adjacent twin-gable roof geometry remain unchanged for one controlled visual retest.

## Intent

Do not replace the roof again until the leaked interior art has been removed from the exterior screenshot. This isolates whether the remaining silhouette problem belongs to the roof family or was primarily visibility contamination.
