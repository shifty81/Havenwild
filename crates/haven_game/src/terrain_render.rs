use haven_assets::autotile::same_autotile_group;
use haven_core::{TavernMap, TileKind, ZoneKind, TILE_SIZE};
use macroquad::prelude::*;

pub(crate) const LPC_SUMMER_TERRAIN_SOURCE_PATH: &str =
    "assets/source/licensed/lpc_revised/Terrain/terrain_summer.png";
pub(crate) const LPC_TERRAIN_V7_SOURCE_PATH: &str =
    "content/assets/lpc/source/lpc-terrains-v7/terrain-v7.png";

const LPC_SOURCE_CELL_SIZE: f32 = 32.0;
const LPC_V7_COLUMNS: u16 = 32;

// Direct pure-fill cells from terrain-v7.tsx. These source-pure cells are
// compatibility fallbacks when the normalized V7 tuple atlas is unavailable.
const LPC_V7_DIRT_TAN: u16 = 97;
const LPC_V7_DIRT_BROWN: u16 = 100;
const LPC_V7_ROCK_DARK: u16 = 112;
const LPC_V7_ROCK_BLACK: u16 = 115;
const LPC_V7_MUD_BROWN: u16 = 124;
const LPC_V7_GRASS: u16 = 321;
const LPC_V7_SOIL: u16 = 333;
const LPC_V7_SAND: u16 = 336;
const LPC_V7_PEBBLE_FILL: u16 = 345;
const LPC_V7_DIRT_ROOTS: u16 = 348;
const LPC_V7_WATER_SHALLOWS_DIRT: u16 = 545;
const LPC_V7_WATER: u16 = 548;
const LPC_V7_WATER_DEEP: u16 = 551;
const LPC_V7_STONE_TAN: u16 = 790;
const LPC_V7_MUDSTONE_BROWN: u16 = 796;
const LPC_V7_WATER_SHALLOWS_SAND: u16 = 837;


/// Presentation-only bridge between semantic highland geology and the active
/// ElizaWy grass-top cliff family. Generated Level-2 cells may retain
/// `MountainRock` as geology/resource semantics, but the broad horizontal cap
/// must visually match the grass crest authored into every active ElizaWy
/// cliff edge. This deliberately does not rewrite the saved terrain tile.
pub(crate) fn structural_cliff_top_presentation_tile(
    map: &TavernMap,
    tile: TileKind,
    x: i32,
    y: i32,
) -> TileKind {
    if tile == TileKind::MountainRock
        && map.get_structural_level(x, y).is_some_and(|level| level > 0)
    {
        TileKind::Grass
    } else {
        tile
    }
}

pub(crate) fn direct_lpc_v7_base_rect(tile: TileKind) -> Option<Rect> {
    let tile_id = match tile {
        TileKind::Grass | TileKind::TallGrass | TileKind::GreenhouseZone => LPC_V7_GRASS,
        TileKind::Dirt => LPC_V7_DIRT_BROWN,
        TileKind::MudBank => LPC_V7_MUD_BROWN,
        TileKind::Road => LPC_V7_DIRT_TAN,
        TileKind::Sand | TileKind::WetSand => LPC_V7_SAND,
        TileKind::PebbleShore => LPC_V7_PEBBLE_FILL,
        TileKind::StonePath => LPC_V7_STONE_TAN,
        TileKind::MountainPath => LPC_V7_DIRT_ROOTS,
        TileKind::MountainRock => LPC_V7_ROCK_DARK,
        TileKind::CaveFloor => LPC_V7_MUDSTONE_BROWN,
        TileKind::TilledSoil | TileKind::Crop => LPC_V7_SOIL,
        TileKind::WateredSoil => LPC_V7_MUD_BROWN,
        TileKind::ShallowWater | TileKind::RiverMouthBlend => LPC_V7_WATER_SHALLOWS_DIRT,
        TileKind::OceanShallow | TileKind::ShoreFoam => LPC_V7_WATER_SHALLOWS_SAND,
        TileKind::Water | TileKind::RiverWater => LPC_V7_WATER,
        TileKind::DeepWater | TileKind::OceanDeep => LPC_V7_WATER_DEEP,
        // Legacy save compatibility only. New generation and F3 authoring
        // never create flat Cliff cells; structural faces use elevation data.
        TileKind::Cliff => LPC_V7_MUDSTONE_BROWN,
        TileKind::CaveWall => LPC_V7_ROCK_BLACK,
        _ => return None,
    };
    Some(lpc_v7_tile_rect(tile_id))
}

pub(crate) fn direct_lpc_v7_map_base_rect(
    map: &TavernMap,
    tile: TileKind,
    x: i32,
    y: i32,
) -> Option<Rect> {
    if !matches!(tile, TileKind::TilledSoil | TileKind::Crop) {
        return direct_lpc_v7_base_rect(tile);
    }

    let same = |nx: i32, ny: i32| matches!(map.get(nx, ny), TileKind::TilledSoil | TileKind::Crop);
    let north = same(x, y - 1);
    let east = same(x + 1, y);
    let south = same(x, y + 1);
    let west = same(x - 1, y);
    let tile_id = match (north, east, south, west) {
        (false, true, true, false) => 300,
        (false, true, true, true) => 301,
        (false, false, true, true) => 302,
        (true, true, true, false) => 332,
        (true, true, true, true) => LPC_V7_SOIL,
        (true, false, true, true) => 334,
        (true, true, false, false) => 364,
        (true, true, false, true) => 365,
        (true, false, false, true) => 366,
        _ => LPC_V7_SOIL,
    };
    Some(lpc_v7_tile_rect(tile_id))
}

fn lpc_v7_tile_rect(tile_id: u16) -> Rect {
    let column = tile_id % LPC_V7_COLUMNS;
    let row = tile_id / LPC_V7_COLUMNS;
    Rect::new(
        f32::from(column) * LPC_SOURCE_CELL_SIZE,
        f32::from(row) * LPC_SOURCE_CELL_SIZE,
        LPC_SOURCE_CELL_SIZE,
        LPC_SOURCE_CELL_SIZE,
    )
}

pub(crate) fn tile_color(tile: TileKind, x: i32, y: i32) -> Color {
    let jitter = tile_jitter(x, y);
    match tile {
        TileKind::Grass => vary(Color::from_rgba(69, 122, 71, 255), jitter),
        TileKind::TallGrass => vary(Color::from_rgba(77, 137, 72, 255), jitter),
        TileKind::Sand => vary(Color::from_rgba(214, 191, 131, 255), jitter * 0.45),
        TileKind::WetSand => vary(Color::from_rgba(174, 151, 111, 255), jitter * 0.35),
        TileKind::PebbleShore => vary(Color::from_rgba(146, 144, 136, 255), jitter * 0.32),
        TileKind::Road => vary(Color::from_rgba(119, 101, 75, 255), jitter * 0.7),
        TileKind::StonePath => vary(Color::from_rgba(126, 120, 107, 255), jitter * 0.45),
        TileKind::MountainPath => vary(Color::from_rgba(123, 116, 98, 255), jitter * 0.45),
        TileKind::WoodFloor => vary(Color::from_rgba(126, 82, 49, 255), jitter * 0.65),
        TileKind::PlankFloor => vary(Color::from_rgba(141, 96, 58, 255), jitter * 0.55),
        TileKind::StoneFloor => vary(Color::from_rgba(111, 116, 121, 255), jitter * 0.55),
        TileKind::BrickFloor => vary(Color::from_rgba(136, 88, 78, 255), jitter * 0.4),
        TileKind::Wall => vary(Color::from_rgba(78, 55, 39, 255), jitter * 0.45),
        TileKind::Cliff => vary(Color::from_rgba(104, 92, 76, 255), jitter * 0.4),
        TileKind::MountainRock => vary(Color::from_rgba(96, 98, 102, 255), jitter * 0.32),
        TileKind::Dirt => vary(Color::from_rgba(98, 70, 47, 255), jitter * 0.75),
        TileKind::Bridge => vary(Color::from_rgba(132, 92, 58, 255), jitter * 0.25),
        TileKind::CaveFloor => vary(Color::from_rgba(76, 72, 70, 255), jitter * 0.7),
        TileKind::CaveWall => vary(Color::from_rgba(39, 40, 43, 255), jitter * 0.45),
        TileKind::TilledSoil => vary(Color::from_rgba(91, 58, 37, 255), jitter * 0.75),
        TileKind::WateredSoil => vary(Color::from_rgba(69, 51, 39, 255), jitter * 0.55),
        TileKind::Crop => vary(Color::from_rgba(76, 162, 75, 255), jitter),
        TileKind::GreenhouseZone => vary(Color::from_rgba(52, 108, 76, 255), jitter * 0.5),
        TileKind::Water => vary(Color::from_rgba(54, 113, 169, 255), jitter * 0.22),
        TileKind::ShallowWater => vary(Color::from_rgba(72, 145, 191, 255), jitter * 0.18),
        TileKind::DeepWater => vary(Color::from_rgba(31, 74, 121, 255), jitter * 0.22),
        TileKind::OceanDeep => vary(Color::from_rgba(18, 54, 94, 255), jitter * 0.18),
        TileKind::OceanShallow => vary(Color::from_rgba(59, 135, 174, 255), jitter * 0.16),
        TileKind::RiverWater => vary(Color::from_rgba(48, 128, 162, 255), jitter * 0.18),
        TileKind::RiverMouthBlend => vary(Color::from_rgba(77, 148, 167, 255), jitter * 0.14),
        TileKind::ShoreFoam => vary(Color::from_rgba(161, 215, 220, 255), jitter * 0.08),
        TileKind::MudBank => vary(Color::from_rgba(95, 75, 53, 255), jitter * 0.45),
    }
}

pub(crate) fn zone_color(zone: ZoneKind) -> Color {
    match zone {
        ZoneKind::None => Color::new(0.0, 0.0, 0.0, 0.0),
        ZoneKind::Tavern => Color::new(1.0, 0.74, 0.22, 0.18),
        ZoneKind::Kitchen => Color::new(1.0, 0.32, 0.22, 0.18),
        ZoneKind::GuestRoom => Color::new(0.45, 0.6, 1.0, 0.18),
        ZoneKind::Cellar => Color::new(0.58, 0.48, 0.72, 0.20),
        ZoneKind::Greenhouse => Color::new(0.33, 1.0, 0.46, 0.20),
        ZoneKind::Field => Color::new(0.62, 0.42, 0.18, 0.18),
        ZoneKind::PublicPath => Color::new(0.55, 0.78, 1.0, 0.18),
        ZoneKind::TavernExterior => Color::new(0.95, 0.64, 0.28, 0.18),
        ZoneKind::Bar => Color::new(0.88, 0.2, 0.18, 0.18),
        ZoneKind::Cave => Color::new(0.35, 0.38, 0.45, 0.20),
        ZoneKind::StaffOnly => Color::new(1.0, 0.92, 0.35, 0.22),
        ZoneKind::CivicLot => Color::new(0.72, 0.64, 1.0, 0.18),
        ZoneKind::MarketLot => Color::new(1.0, 0.58, 0.18, 0.18),
        ZoneKind::ResidentialLot => Color::new(0.42, 0.72, 1.0, 0.18),
        ZoneKind::ArtisanLot => Color::new(0.86, 0.48, 0.22, 0.18),
        ZoneKind::HarborLot => Color::new(0.22, 0.68, 0.88, 0.20),
        ZoneKind::AgriculturalLot => Color::new(0.52, 0.82, 0.30, 0.18),
    }
}

pub(crate) fn draw_tile_detail(
    _map: &TavernMap,
    tile: TileKind,
    _x: i32,
    _y: i32,
    px: f32,
    py: f32,
) {
    // Source-backed natural terrain never receives procedural marks. V7 fill
    // detail must come from an audited single-cell variant, while larger
    // authored details are placed atomically as objects or stamps. This
    // compatibility path is limited to constructed/gameplay surfaces that may
    // still render without a mounted project atlas.
    match tile {
        TileKind::Bridge | TileKind::WoodFloor | TileKind::PlankFloor => {
            for i in 0..3 {
                let bx = px + 6.0 + i as f32 * 9.0;
                draw_line(
                    bx,
                    py + 4.0,
                    bx,
                    py + TILE_SIZE - 4.0,
                    1.0,
                    Color::new(0.24, 0.13, 0.08, 0.30),
                );
            }
        }
        TileKind::StoneFloor | TileKind::BrickFloor => {
            draw_rectangle_lines(
                px + 2.0,
                py + 2.0,
                TILE_SIZE - 4.0,
                TILE_SIZE - 4.0,
                1.0,
                Color::new(0.18, 0.20, 0.24, 0.18),
            );
        }
        TileKind::Crop => {
            draw_circle(px + 12.0, py + 20.0, 4.0, Color::new(0.26, 0.56, 0.24, 0.9));
            draw_circle(
                px + 20.0,
                py + 16.0,
                5.0,
                Color::new(0.34, 0.70, 0.26, 0.92),
            );
        }
        TileKind::GreenhouseZone => {
            draw_line(
                px + 4.0,
                py + 4.0,
                px + 28.0,
                py + 28.0,
                1.0,
                Color::new(0.7, 1.0, 0.75, 0.18),
            );
            draw_line(
                px + 28.0,
                py + 4.0,
                px + 4.0,
                py + 28.0,
                1.0,
                Color::new(0.7, 1.0, 0.75, 0.12),
            );
        }
        _ => {}
    }
}

pub(crate) fn draw_tile_border(map: &TavernMap, tile: TileKind, x: i32, y: i32, px: f32, py: f32) {
    let color = Color::new(0.0, 0.0, 0.0, 0.11);
    if tile.autotile_group().is_none() {
        draw_rectangle_lines(px, py, TILE_SIZE, TILE_SIZE, 1.0, color);
        return;
    }
    if !same_autotile_group(map, tile, x, y - 1) {
        draw_line(px, py, px + TILE_SIZE, py, 1.0, color);
    }
    if !same_autotile_group(map, tile, x - 1, y) {
        draw_line(px, py, px, py + TILE_SIZE, 1.0, color);
    }
    if !same_autotile_group(map, tile, x + 1, y) {
        draw_line(
            px + TILE_SIZE,
            py,
            px + TILE_SIZE,
            py + TILE_SIZE,
            1.0,
            color,
        );
    }
    if !same_autotile_group(map, tile, x, y + 1) {
        draw_line(
            px,
            py + TILE_SIZE,
            px + TILE_SIZE,
            py + TILE_SIZE,
            1.0,
            color,
        );
    }
}

fn hash2(x: i32, y: i32) -> u32 {
    let mut n = x as u32;
    n = n
        .wrapping_mul(374_761_393)
        .wrapping_add((y as u32).wrapping_mul(668_265_263));
    n ^ (n >> 13)
}

pub(crate) fn tile_jitter(x: i32, y: i32) -> f32 {
    (hash2(x, y) % 100) as f32 / 100.0 - 0.5
}

fn vary(color: Color, amount: f32) -> Color {
    let delta = amount * 0.08;
    Color::new(
        (color.r + delta).clamp(0.0, 1.0),
        (color.g + delta).clamp(0.0, 1.0),
        (color.b + delta).clamp(0.0, 1.0),
        color.a,
    )
}

#[cfg(test)]
mod direct_lpc_tests {
    use super::*;

    #[test]
    fn direct_v7_fallback_covers_active_source_pure_terrain_roles() {
        for tile in [
            TileKind::Grass,
            TileKind::TallGrass,
            TileKind::Dirt,
            TileKind::Road,
            TileKind::MudBank,
            TileKind::Sand,
            TileKind::WetSand,
            TileKind::PebbleShore,
            TileKind::StonePath,
            TileKind::MountainPath,
            TileKind::MountainRock,
            TileKind::CaveFloor,
            TileKind::TilledSoil,
            TileKind::Crop,
            TileKind::WateredSoil,
            TileKind::Water,
            TileKind::ShallowWater,
            TileKind::DeepWater,
            TileKind::OceanShallow,
            TileKind::OceanDeep,
            TileKind::RiverWater,
            TileKind::RiverMouthBlend,
        ] {
            let rect = direct_lpc_v7_base_rect(tile)
                .unwrap_or_else(|| panic!("missing terrain-v7 fallback for {tile:?}"));
            assert_eq!(rect.w, LPC_SOURCE_CELL_SIZE);
            assert_eq!(rect.h, LPC_SOURCE_CELL_SIZE);
            assert!(rect.x >= 0.0 && rect.x + rect.w <= 1024.0);
            assert!(rect.y >= 0.0 && rect.y + rect.h <= 2048.0);
        }
    }

    #[test]
    fn structural_mountain_rock_uses_grass_top_presentation_without_rewriting_semantics() {
        let mut map = TavernMap::empty_with(TileKind::MountainRock);
        map.set_structural_level(4, 5, Some(2));
        assert_eq!(
            structural_cliff_top_presentation_tile(&map, TileKind::MountainRock, 4, 5),
            TileKind::Grass
        );
        assert_eq!(map.get(4, 5), TileKind::MountainRock);

        map.set_structural_level(4, 5, Some(0));
        assert_eq!(
            structural_cliff_top_presentation_tile(&map, TileKind::MountainRock, 4, 5),
            TileKind::MountainRock
        );
    }

    #[test]
    fn constructed_terrain_remains_owned_by_dedicated_renderers() {
        assert!(direct_lpc_v7_base_rect(TileKind::WoodFloor).is_none());
        assert!(direct_lpc_v7_base_rect(TileKind::Wall).is_none());
    }
}
