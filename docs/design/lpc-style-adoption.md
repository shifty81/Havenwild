# Havenwild LPC Style Adoption

Reference: https://lpc.opengameart.org/static/LPC-Style-Guide/build/styleguide.html

Extended production rules: `docs/design/pixel-art-production-standard.md`

LPC is adopted as a compatibility and visual-reference standard for Havenwild
terrain, farming content, UI, and prototype props. It is not adopted wholesale
as the final character contract.

## Adopt directly

- 32x32 primary tile grid with optional 16x16 subtiles.
- Orthographic rendering with an approximately 60-degree top-down view.
- No perspective scaling or isometric projection.
- Medium-low texture density and quiet center tiles.
- Detail concentrated at material edges, corners, and occasional variation tiles.
- Mostly overhead lighting with mild left-side directionality.
- Yellow-shifted highlights and purple-shifted shadows.
- Colored outlines rather than pure black for terrain and props.
- Projected prop shadows using `#322125` at approximately 60% opacity.
- Props must contrast with the terrain beneath them.

## Adapt for Havenwild

- LPC four-direction character sheets are accepted for the playable prototype
  through explicit adapters. Havenwild may later add taller/eight-direction
  characters without invalidating the LPC prototype contract.
- LPC props require Havenwild visual, collision, interaction, occlusion, and
  bottom-foot anchor metadata before runtime promotion.
- LPC edge tiles must enter the neighbor-mask/autotile pipeline; complete preview
  tiles must never be applied as transparent overlays.
- 16x16 assets are scaled to 32x32 with nearest-neighbor sampling only when their
  source record and adapter explicitly permit it.

## Runtime acceptance checklist

1. Verify source, creator, selected license, and attribution.
2. Verify the visible sheet contents rather than trusting its filename.
3. Record grid size, cell rectangles, animation order, and anchor points.
4. Keep terrain centers subtle and provide edge/corner masks plus variations.
5. Validate orthographic perspective and eliminate diagonal/isometric roof faces.
6. Confirm the asset cannot be exported as a standalone third-party asset pack.
