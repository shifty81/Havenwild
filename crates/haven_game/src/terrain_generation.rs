use haven_core::{SceneBiome, SceneKind, TileInteraction, TileKind, MAP_H, MAP_W};

fn hash2(x: i32, y: i32) -> u32 {
    let mut n = x as u32;
    n = n
        .wrapping_mul(374_761_393)
        .wrapping_add((y as u32).wrapping_mul(668_265_263));
    n ^ (n >> 13)
}

pub(crate) fn default_interaction_for_tile(tile: TileKind) -> TileInteraction {
    tile.default_interaction()
}

pub(crate) fn terrain_height(seed: u32, x: i32, y: i32) -> u32 {
    let coarse = hash2(x / 4 + (seed % 97) as i32, y / 4 + ((seed / 3) % 89) as i32) % 44;
    let mid = hash2(
        x / 2 + ((seed / 5) % 71) as i32,
        y / 2 + ((seed / 7) % 67) as i32,
    ) % 34;
    let fine = hash2(x + seed as i32, y - seed as i32) % 22;
    coarse + mid + fine
}

pub(crate) struct TerrainClassificationInput {
    pub scene_kind: SceneKind,
    pub biome: SceneBiome,
    pub height: i32,
    pub edge: i32,
    pub x: i32,
    pub y: i32,
    pub water_level: i32,
    pub mountain_level: i32,
}

pub(crate) fn classify_height_tile(input: TerrainClassificationInput) -> TileKind {
    let TerrainClassificationInput {
        scene_kind,
        biome,
        height,
        edge,
        x,
        y,
        water_level,
        mountain_level,
    } = input;
    if scene_kind == SceneKind::Interior {
        return if x == 0 || y == 0 || x == MAP_W as i32 - 1 || y == MAP_H as i32 - 1 {
            TileKind::Wall
        } else {
            TileKind::WoodFloor
        };
    }

    if scene_kind == SceneKind::Cave {
        return if edge < 1 || height >= mountain_level {
            TileKind::CaveWall
        } else if height <= water_level - 6 {
            TileKind::DeepWater
        } else if height <= water_level {
            TileKind::ShallowWater
        } else {
            TileKind::CaveFloor
        };
    }

    let seed = hash2(x + height, y + water_level);
    // Absolute elevation selects the horizontal plateau material only.
    // Vertical cliff faces are derived separately from neighboring height
    // differences and must never replace a ground cell with a flat Cliff tile.
    if edge < 1 || height >= mountain_level {
        return TileKind::MountainRock;
    }
    if height <= water_level - 10 {
        return TileKind::DeepWater;
    }
    if height <= water_level {
        return TileKind::ShallowWater;
    }
    if height <= water_level + 4 {
        return match biome {
            SceneBiome::Coastal => TileKind::Sand,
            SceneBiome::Highlands => TileKind::PebbleShore,
            _ => TileKind::Dirt,
        };
    }
    if height <= water_level + 10 {
        return match biome {
            SceneBiome::Coastal => TileKind::Sand,
            SceneBiome::Highlands => TileKind::PebbleShore,
            _ => TileKind::Dirt,
        };
    }
    if biome == SceneBiome::Highlands && height >= mountain_level - 10 {
        // MountainPath is a traversal/road semantic, not a generic highland
        // material. Procedural ramps/connectors own it explicitly.
        return TileKind::PebbleShore;
    }
    if biome == SceneBiome::Coastal && height <= water_level + 16 {
        return if seed.is_multiple_of(5) {
            TileKind::PebbleShore
        } else {
            TileKind::Sand
        };
    }
    if seed.is_multiple_of(5) {
        TileKind::TallGrass
    } else {
        TileKind::Grass
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn exterior_height_classification_never_returns_flat_cliff_tiles() {
        for biome in [
            SceneBiome::Temperate,
            SceneBiome::Coastal,
            SceneBiome::Highlands,
        ] {
            for height in 0..=120 {
                let tile = classify_height_tile(TerrainClassificationInput {
                    scene_kind: SceneKind::Exterior,
                    biome,
                    height,
                    edge: 8,
                    x: 12,
                    y: 12,
                    water_level: 36,
                    mountain_level: 76,
                });
                assert_ne!(tile, TileKind::Cliff);
            }
        }
    }

    #[test]
    fn highland_rockline_selects_horizontal_rock_ground() {
        let tile = classify_height_tile(TerrainClassificationInput {
            scene_kind: SceneKind::Exterior,
            biome: SceneBiome::Highlands,
            height: 76,
            edge: 8,
            x: 12,
            y: 12,
            water_level: 36,
            mountain_level: 76,
        });
        assert_eq!(tile, TileKind::MountainRock);
    }
}
