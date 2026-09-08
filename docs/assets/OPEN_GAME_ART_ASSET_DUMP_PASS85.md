# OpenGameArt Asset Dump - Pass 85

This pass records the newly supplied OpenGameArt/LPC dump for planning and
keeps the raw third-party files out of normal source rollups.

## Uploaded Sources

| File | Contents | Immediate Lane |
| --- | --- | --- |
| `1.zip` | 37 PNGs, 4 nested ZIPs, 4 credit text files. Includes bat wings, cats/dogs, castle sheets, wood sheets, portraits, crops, children, furniture credits, skin tones. | Intake/catalog only |
| `2.zip` | 32 PNGs, 4 nested ZIPs. Includes EULPC body/head/feet/legs/torso/hair/wing sheets, feathered-wing animation sheets, goat, gentleman and goggles nested packs. | Intake/catalog only |
| `lpc_revised_character_basics.zip` | 14,723 entries; 12,606 PNGs plus GIF/INI/TXT support files. Main coverage is revised LPC body, head, clothing, and hair animation sheets. | Character/animation planning |
| `credits (1)(1).txt` | Simple shirts credits/license notes. | Attribution source |
| `credits (2)(1).txt` | Hair credits/license notes. | Attribution source |
| `credits (3)(1).txt` | Body/head/expression credits/license notes. | Attribution source |

## Utilization Plan

- Character bodies, heads, clothing, hair, wings, and socks/shoes should feed
  the future LPC character-builder and animation-studio pipeline.
- Castle, wood, crop, furniture, creature, portrait, and animal sheets should be
  cataloged as reference/intake packs first, then promoted only through an
  explicit license-reviewed asset lane.
- Portraits can guide NPC profile and dialogue UI planning, but should not be
  shipped directly until style and license review are complete.
- The current terrain autotiling work should continue from the project-owned
  Havenwild/LPC environment tiles already promoted into `common_base_terrain_32`
  and the live autotile atlas.

## License Notes

The supplied credits mention mixed OpenGameArt licenses, including OGA-BY,
CC-BY, CC-BY-SA, GPL, and CC0 depending on asset and contributor. Keep these
assets in the intake/reference lane until each promoted runtime asset has:

- source file reference
- author attribution
- exact license
- compatible use lane
- generated/promoted derivative metadata

This is especially important for CC-BY-SA and GPL-family assets, which may
carry share-alike or source-distribution obligations.

## Runtime Promotion Priority

1. Finish LPC environment autotiling and World Editor terrain workflow.
2. Add character-builder cataloging for revised LPC bodies, heads, hair, and
   clothing.
3. Add animal/creature sheets to a creature animation catalog.
4. Promote furniture/building/castle/crop sheets only after they are normalized
   into Havenwild's object/stamp system and attribution records exist.
