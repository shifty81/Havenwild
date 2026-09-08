# Pass 140 — Character Sprite Runtime

Adds the normalized 64x64 LPC layered-sprite registry and Macroquad preview renderer. Character options resolve through semantic IDs into texture paths, direction rows, animation columns, layer order, and palette channels. Missing promoted textures are reported visibly rather than silently replaced.

This pass intentionally does not ship third-party LPC art. The registry targets Havenwild-generated/promoted character textures under `assets/generated/characters/`; those outputs must be produced from license-approved sources or authored in Pixel Studio.
