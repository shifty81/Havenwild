# Cozy Tavern Aesthetic Roadmap

Date: 2026-05-24

## Target Feeling

Warm, hand-built, practical, slightly magical, and alive. The tavern should feel like a working place that becomes more comfortable through the player's care.

## Art Direction Rules

### Palette

- Use warm interiors: honey wood, amber candlelight, muted red cloth, copper, cream, moss green.
- Use cooler exteriors: blue-green shadows, desaturated night blues, soft fog, seasonal accents.
- Keep saturation controlled. Important interactables can be more saturated than background tiles.
- Avoid single-hue dominance. Cozy tavern scenes need contrast between wood, cloth, stone, plant life, firelight, and UI.

### Lighting

- Treat lighting as mood and readability, not realism.
- Add warm window/candle/fire pools indoors.
- Add soft outdoor time-of-day tint: morning gold, midday neutral, evening rose, night blue.
- Make build-mode overlays bright but gentle: green valid zones, red invalid zones, amber selected tiles.

### Shape Language

- Furniture should be chunky and readable at a glance.
- Corners can be softened through pixel clusters and highlight pixels, not necessarily literal rounded UI.
- Important objects need silhouettes: bar, keg, table, bed, stove, greenhouse marker, crops, doors.

### Motion

- Cozy scenes need idle motion: fire flicker, candle shimmer, crop sway, customer head turns, steam, dust motes, tavern sign swing.
- Player and customers should have readable walk cycles with small bobbing and foot timing.
- Work actions need tactile feedback: hoe thump, tile pop, sawdust/soil particles, item pickup glint.

### Texture

- Every tile type needs at least three visual variants before it will stop feeling synthetic.
- Wood floor: plank offsets, knots, edge highlights.
- Stone floor: chips, cool shadows, slight color variation.
- Soil: clumps, moisture states, tilled furrows.
- Greenhouse: glass ribs, mist, plant trays, warm/cool mixed lighting.

### UI

- UI should feel like a tavern ledger/workbench, not a sterile debug tool.
- Use high contrast for important numbers and states.
- Use icon-first controls where possible: coin, reputation, open/closed, clock, build mode, comfort, dirt, stock.
- Editor panels should stay utilitarian but still share the same palette.

## Required Asset Families

### Environment

- Ground: grass, road, mud, snow, flower patches.
- Floors: wood, stone, kitchen tile, cellar stone, greenhouse decking.
- Walls: exterior, interior, kitchen, cellar, upstairs.
- Doors/windows: seasonal variants and lit/unlit states.
- Lighting: candles, lanterns, fireplace, window glow, wall sconces.

### Tavern Objects

- Tables, chairs, benches, bar counters, shelves, kegs, taps, barrels, crates.
- Kitchen stations: stove, prep table, pantry, sink, storage.
- Guest rooms: beds, side tables, rugs, wardrobes, wall decor.
- Cleanliness: dirt piles, spills, broken mugs, swept/clean variants.

### Farming/Greenhouse

- Tilled soil states: dry, wet, seeded, sprout, mature, harvested.
- Greenhouse zone marker, glass panels, planters, irrigation/sprinkler pieces.
- Crops by growth stage, but use original crop names and art.

### Characters

- Player base body: head, hair, torso, arms, legs, outfit layers.
- Customer archetypes: traveler, merchant, worker, noble, local regular.
- Staff roles: server, cook, cleaner, guard-like role under original naming.
- Emotion states: neutral, pleased, impatient, angry, drunk/tired if used.

### Effects

- Dust, steam, spark, food aroma, spilled liquid, coin sparkle, reputation pop.
- Construction placement poof, invalid placement shake, greenhouse mist.

## Implementation Priorities

1. Establish a 32x32 tile visual standard with 16x16/32x48 object exceptions.
2. Add tile variant selection by deterministic coordinate hash.
3. Add time-of-day lighting and simple local light sources.
4. Replace procedural object blocks with sprite-backed objects.
5. Add animated customers and player sprite layers.
6. Add UI icon sheet and panel skin.
7. Add weather/season overlay states.

## References

- Cozy game definitions commonly emphasize gentle challenge, complementary colors, and mindful music.
- Pixel-art production should use limited palettes, controlled contrast, and clear silhouettes.
- Game UI needs high contrast and hue differentiation for fast reading.
- Travellers Rest public-facing references point to a warm tavern/farm/crafting loop, but our assets, names, UI, maps, writing, and implementation must remain original.
