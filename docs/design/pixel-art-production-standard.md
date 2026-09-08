# Havenwild Pixel-Art Production Standard

These OpenGameArt tutorial chapters are adopted as working references:

- https://opengameart.org/content/chapter-1-the-right-tools
- https://opengameart.org/content/chapter-3-perspectives
- https://opengameart.org/content/chapter-4-shadow-and-light
- https://opengameart.org/content/chapter-5-color-palettes
- https://opengameart.org/content/chapter-6-anti-aliasing
- https://opengameart.org/content/chapter-7-textures-and-dithering
- https://opengameart.org/content/chapter-8-a-world-of-tiles

## Authoring rules

### Tools

- The editor must support palettes, transparency, layers, nearest-neighbor
  zoom, animation preview, and repeating-tile preview.
- Automatic smoothing, resampling, and destructive anti-aliasing stay disabled.
- PNG is the canonical raster format for runtime pixel art.

### Perspective

- Havenwild uses one fixed orthographic 3/4 convention.
- Horizontal planes are viewed from above; vertical planes are viewed from the
  front. Parallel lines do not converge and distant objects do not shrink.
- Do not mix isometric diagonals, planometric axes, or perspective roof faces
  into orthographic scene art.
- Every structure/prop preview should expose a perspective guide and bottom-foot
  anchor before promotion.

### Light and shadow

- Every asset declares one consistent light direction; the default is overhead
  with a mild leftward bias.
- Highlights and shadows describe volume, not decorative noise.
- Cast shadows use the LPC/Havenwild shadow family (`#322125`, approximately
  60% opacity) unless a scene-specific lighting profile overrides it.
- Neighboring objects and roof overhangs may cast shadows, but those shadows must
  not change collision or interaction footprints.

### Palettes

- Establish the palette before detailed rendering and refine it throughout.
- Use small, reusable HSL-oriented ramps rather than independent RGB colors.
- Shift highlights warmer/yellower and shadows cooler/purpler.
- Terrain, props, characters, and UI each need enough value separation to remain
  readable when composited together.
- Pure black, pure white, and maximum-saturation colors require an explicit
  effect/UI exception.

### Anti-aliasing

- Use hand-placed buffer shades only between known adjacent colors.
- Do not pre-blend a sprite edge against an unknown background.
- Anti-aliasing must preserve the original silhouette and pixel clusters.
- Runtime texture filtering remains nearest-neighbor.

### Texture and dithering

- Texture communicates material response to light: wood grain, stone chips,
  soil clumps, grass tufts, and similar authored clusters.
- Avoid random single-pixel noise and excessive texture density.
- Dithering is optional and normally reserved for large gradients or deliberately
  rough surfaces; it is not a default sprite or terrain treatment.
- Center tiles stay quiet. Strong detail belongs on transition edges, objects,
  landmarks, and sparse variation tiles.

### Tiles and transitions

- Each terrain family provides multiple center variations to suppress visible
  repetition.
- Variations use coherent clusters, not random pixels.
- Edge/corner tiles are validated in a repeated 3x3 and 5x5 preview.
- Coastlines and material boundaries require cardinal edges, outer corners,
  inner corners, and isolated/surrounded cases.
- Complete example/composite tiles must never be mistaken for alpha masks.
- Tile previews must test adjacency against every compatible terrain family.

## Editor overlay requirements

The asset/editor workflow should expose these as task-oriented tools:

1. **Palette**: reusable ramps, hue/value inspection, and color-count warnings.
2. **Perspective**: orthographic axes, anchor, footprint, and roof-plane checks.
3. **Lighting**: light-direction and cast-shadow preview.
4. **Tile repeat**: 3x3/5x5 repetition and seam detection.
5. **Autotile cases**: cardinal/inner/outer corner matrix with missing-case warnings.
6. **Texture density**: center/edge variation preview and noise warnings.
7. **Animation**: direction-row and frame-timing preview.

These tools belong behind clear authoring workflows, not as unrelated debug tabs.

