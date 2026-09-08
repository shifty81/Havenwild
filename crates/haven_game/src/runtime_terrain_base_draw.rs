use haven_assets::{
    asset_registry::tile_asset_rect, live_autotile_atlas::live_autotile_atlas_entry,
    lpc_mapped_terrain::LpcMappedTerrainEntry,
};
use haven_core::{TavernMap, TileAutoGroup, TileKind, MAP_W, TILE_SIZE};
use haven_render::atlas_rect;
use haven_world::TERRAIN_TUPLE_RENDER_OFFSET_TILES;
use macroquad::prelude::*;

use crate::terrain_render::{
    direct_lpc_v7_map_base_rect, structural_cliff_top_presentation_tile, tile_color,
};
use crate::{bridge_render, Game};

pub(crate) struct TerrainBaseDrawRequest<'a> {
    pub map: &'a TavernMap,
    pub tile: TileKind,
    pub x: i32,
    pub y: i32,
    pub screen: Vec2,
    pub resolved_base: Option<(TileAutoGroup, u8)>,
    pub mapped_entry: Option<LpcMappedTerrainEntry>,
    pub global: Option<(i32, i32)>,
}

impl Game {
    pub(crate) fn draw_tile_base(&self, request: TerrainBaseDrawRequest<'_>) {
        let TerrainBaseDrawRequest {
            map,
            tile,
            x,
            y,
            screen,
            resolved_base,
            mapped_entry,
            global,
        } = request;
        if tile == TileKind::WoodFloor && self.draw_enclosed_house_floor_skin(screen) {
            return;
        }
        if tile == TileKind::Wall && self.draw_enclosed_house_wall_skin(x, y, screen) {
            return;
        }
        // H20 live visual acceptance: the active structural cliff family is
        // grass-topped ElizaWy art. A V7 gray MountainRock fill underneath
        // those crests creates a hard cross-family seam, so elevated semantic
        // MountainRock uses a grass-compatible cap presentation. Geology and
        // resource semantics remain MountainRock in the saved map.
        let presentation_tile = self.runtime_terrain_presentation_tile(map, tile, x, y, global);
        if presentation_tile != tile {
            if let Some(texture) = &self.lpc_terrain_v7_source {
                if let Some(source) = direct_lpc_v7_map_base_rect(map, presentation_tile, x, y) {
                    draw_texture_ex(
                        texture,
                        screen.x,
                        screen.y,
                        WHITE,
                        DrawTextureParams {
                            dest_size: Some(vec2(TILE_SIZE, TILE_SIZE)),
                            source: Some(source),
                            ..Default::default()
                        },
                    );
                    return;
                }
            }
        }

        if tile == TileKind::Bridge
            && bridge_render::draw_bridge_base(
                map,
                x,
                y,
                screen.x,
                screen.y,
                self.lpc_bridge_source.as_ref(),
                self.lpc_mapped_terrain_atlas.as_ref(),
            )
        {
            return;
        }

        // Use the exact authored terrain-map-v7 tuple first. This atlas is a
        // compiled view of the committed LPC tile sheets; it already contains
        // the correct edge, outer-corner, inner-corner, isolated, and dirt/sand
        // transition shapes. Direct source-sheet cells remain a fallback for
        // semantic roles that the v7 tuple atlas does not cover.
        if let (Some(texture), Some(entry)) = (self.lpc_mapped_terrain_atlas.as_ref(), mapped_entry)
        {
            draw_texture_ex(
                texture,
                screen.x,
                screen.y,
                WHITE,
                DrawTextureParams {
                    dest_size: Some(vec2(TILE_SIZE, TILE_SIZE)),
                    source: Some(atlas_rect(entry.rect)),
                    ..Default::default()
                },
            );
            return;
        }

        // The active V7 lane never falls through to ElizaWy terrain cells.
        // Semantic roles absent from the mapped tuple atlas may use reviewed
        // direct terrain-v7 fills, but unsupported V7 contacts remain visible
        // as pure owner fills and diagnostics rather than cross-family art.
        if let Some(texture) = &self.lpc_terrain_v7_source {
            if let Some(source) = direct_lpc_v7_map_base_rect(map, tile, x, y) {
                draw_texture_ex(
                    texture,
                    screen.x,
                    screen.y,
                    WHITE,
                    DrawTextureParams {
                        dest_size: Some(vec2(TILE_SIZE, TILE_SIZE)),
                        source: Some(source),
                        ..Default::default()
                    },
                );
                return;
            }
        }

        // Compatibility path for projects that do not mount the authored LPC
        // tuple atlas. Water is intentionally left to the water fallback lane.
        if tile.is_water() {
            return;
        }
        if let Some((group, mask)) =
            resolved_base.filter(|(group, _)| *group != TileAutoGroup::Water)
        {
            if let (Some(texture), Some(entry)) = (
                self.live_autotile_atlas.as_ref(),
                live_autotile_atlas_entry(group, mask),
            ) {
                draw_texture_ex(
                    texture,
                    screen.x,
                    screen.y,
                    WHITE,
                    DrawTextureParams {
                        dest_size: Some(vec2(TILE_SIZE, TILE_SIZE)),
                        source: Some(atlas_rect(entry.rect)),
                        ..Default::default()
                    },
                );
                return;
            }
        }
        if let Some(texture) = &self.terrain_atlas {
            draw_texture_ex(
                texture,
                screen.x,
                screen.y,
                WHITE,
                DrawTextureParams {
                    dest_size: Some(vec2(TILE_SIZE, TILE_SIZE)),
                    source: Some(atlas_rect(tile_asset_rect(tile, x, y))),
                    ..Default::default()
                },
            );
            return;
        }
        draw_rectangle(
            screen.x,
            screen.y,
            TILE_SIZE,
            TILE_SIZE,
            tile_color(tile, x, y),
        );
    }

    /// Runtime presentation bridge for semantic terrain that participates in a
    /// complete authored cliff ramp. The six MountainPath cells are traversal
    /// connector semantics, not a request to draw brown path tiles underneath
    /// the transparent pixels of the LPC 3x4 ramp stamp. Present those corridor
    /// cells as grass so the complete authored ramp owns the visible diagonal.
    pub(crate) fn runtime_terrain_presentation_tile(
        &self,
        map: &TavernMap,
        tile: TileKind,
        x: i32,
        y: i32,
        global: Option<(i32, i32)>,
    ) -> TileKind {
        let structural = structural_cliff_top_presentation_tile(map, tile, x, y);
        if tile != TileKind::MountainPath {
            return structural;
        }
        let global = global.or_else(|| {
            self.active_surface_chunk_coord().map(|chunk| {
                (
                    chunk.x * MAP_W as i32 + x,
                    chunk.y * haven_core::MAP_H as i32 + y,
                )
            })
        });
        if global.is_some_and(|(global_x, global_y)| {
            self.surface_authored_ramp_owner(global_x, global_y).is_some()
        }) {
            TileKind::Grass
        } else {
            structural
        }
    }


    fn draw_enclosed_house_floor_skin(&self, screen: Vec2) -> bool {
        if self.world.active().kind != haven_core::SceneKind::Interior {
            return false;
        }
        self.draw_enclosed_house_structure_asset(
            "floor_wood_herringbone_light",
            screen,
        )
    }

    fn draw_enclosed_house_wall_skin(&self, x: i32, y: i32, screen: Vec2) -> bool {
        let scene = self.world.active();
        if scene.kind != haven_core::SceneKind::Interior {
            return false;
        }
        let Some(presentation) = haven_core::resolve_house_interior_wall_presentation(scene, x, y) else {
            return false;
        };
        if presentation == haven_core::HouseInteriorWallPresentation::SouthFacingBody {
            return self.draw_enclosed_house_structure_asset("wall_drywall_simple", screen);
        }

        // W57K8: side/front shell cells are collision-only in house interiors.
        // Repeating the 32x32 CutawayOverlay source on every perimeter tile made
        // the room read as stacked horizontal rails. Treat those cells as an
        // intentionally open camera cut until a certified side/front trim family
        // is authored. Returning true suppresses generic terrain fallback.
        true
    }

    fn draw_enclosed_house_structure_asset(&self, asset_id: &str, screen: Vec2) -> bool {
        let Some(definition) = self.placeable_registry.resolve_alias(asset_id) else {
            return false;
        };
        let (Some(texture), Some(visual)) = (
            self.placeable_textures.get(definition.pack_qualified_id()),
            definition.visual.as_ref(),
        ) else {
            return false;
        };
        let Some(frame) = visual.frame_for_state(Some("default")) else {
            return false;
        };
        draw_texture_ex(
            texture,
            screen.x + TILE_SIZE * 0.5 - visual.foot_anchor[0] + frame.draw_offset_px[0],
            screen.y + TILE_SIZE - visual.foot_anchor[1] + frame.draw_offset_px[1],
            WHITE,
            DrawTextureParams {
                dest_size: Some(vec2(frame.source_rect[2], frame.source_rect[3])),
                source: Some(Rect::new(
                    frame.source_rect[0],
                    frame.source_rect[1],
                    frame.source_rect[2],
                    frame.source_rect[3],
                )),
                ..Default::default()
            },
        );
        true
    }

    pub(crate) fn draw_mapped_terrain_tuple_overlay(
        &self,
        entry: LpcMappedTerrainEntry,
        screen: Vec2,
    ) {
        let Some(texture) = self.lpc_mapped_terrain_atlas.as_ref() else {
            return;
        };
        debug_assert!(entry.is_mixed);
        let offset = TILE_SIZE * TERRAIN_TUPLE_RENDER_OFFSET_TILES;
        draw_texture_ex(
            texture,
            screen.x + offset,
            screen.y + offset,
            WHITE,
            DrawTextureParams {
                dest_size: Some(vec2(TILE_SIZE, TILE_SIZE)),
                source: Some(atlas_rect(entry.rect)),
                ..Default::default()
            },
        );
    }
}
