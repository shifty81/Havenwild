use super::*;
use haven_render::object_foot_world;

impl Game {
    pub(super) fn draw_object(&self, object: PlacedObject, screen_origin: Vec2) {
        self.draw_object_for_scene(
            self.world.active(),
            object,
            Vec2::ZERO,
            false,
            screen_origin,
        );
    }

    pub(super) fn draw_surface_object(
        &self,
        scene: &SceneMap,
        object: PlacedObject,
        chunk_x: i32,
        chunk_y: i32,
    ) {
        let offset = vec2(
            chunk_x as f32 * MAP_W as f32 * TILE_SIZE,
            chunk_y as f32 * MAP_H as f32 * TILE_SIZE,
        );
        let fallback_origin = self.runtime_world_to_screen(offset + object_origin(object));
        self.draw_object_for_scene(scene, object, offset, true, fallback_origin);
    }

    fn draw_object_for_scene(
        &self,
        scene: &SceneMap,
        object: PlacedObject,
        offset: Vec2,
        global_surface: bool,
        screen_origin: Vec2,
    ) {
        let object_state = scene.map.object_state(object.id);
        if global_surface
            && scene.kind == SceneKind::Exterior
            && object.kind == ObjectKind::Stairs
            && object_state.is_some_and(|state| state.eq_ignore_ascii_case("ladder"))
        {
            // Generated coastal ladders are semantic structural connectors.
            // The cliff renderer owns their exact integrated ladder artwork;
            // drawing the generic published Stairs asset here produces the
            // gray porch/front-door stair cap seen on top of cliff ladders.
            return;
        }

        if object.kind == ObjectKind::CaveEntrance && scene.kind == SceneKind::Exterior {
            let manifest = haven_world::ContinuousSurfaceManifest::for_world(&self.world);
            let chunk = manifest
                .chunk_for_scene(&scene.id)
                .unwrap_or(haven_world::open_world::ChunkCoord::new(0, 0));
            let global_x = chunk.x * MAP_W as i32 + object.x;
            let global_y = chunk.y * MAP_H as i32 + object.y;
            let consumed_by_structural_cliff = self
                .surface_structural_at_global(global_x, global_y)
                .is_some_and(|cell| {
                    cell.cave_host_eligible
                        && cell.exposed_edges.contains(haven_world::EdgeMaskV2::SOUTH)
                });
            if consumed_by_structural_cliff {
                // Structural cliff projection owns the exact 1x3 source envelope.
                // Its aperture is 1x2; the third row is the ground threshold.
                return;
            }
        }

        // R1 visual-authority rule: manifest-backed natural objects use the
        // audited generated object atlas before legacy/published gameplay adapters.
        // The legacy `tree_default` placeable intentionally stores gameplay state
        // only, but its historical 32x64 visual frame is transparent against the
        // current 160x192 atlas. Letting that adapter win produced live Tree
        // collision with no pixels on screen.
        let canonical_natural_visual = matches!(
            object.kind,
            ObjectKind::Tree
                | ObjectKind::Bush
                | ObjectKind::Boulder
                | ObjectKind::OreNode
                | ObjectKind::Mushroom
                | ObjectKind::Herb
                | ObjectKind::Stump
                | ObjectKind::Log
        );
        if canonical_natural_visual {
            if let (Some(texture), Some(entry)) = (
                &self.object_atlas,
                object_asset_entry_for_cell(object.kind, object.x, object.y),
            ) {
                let foot = object_foot_world(object) + offset;
                let foot = if global_surface {
                    self.runtime_world_to_screen(foot)
                } else {
                    self.world_to_screen(foot)
                };
                draw_texture_ex(
                    texture,
                    foot.x - entry.foot_anchor.0,
                    foot.y - entry.foot_anchor.1,
                    WHITE,
                    DrawTextureParams {
                        dest_size: Some(vec2(entry.rect.w, entry.rect.h)),
                        source: Some(atlas_rect(entry.rect)),
                        ..Default::default()
                    },
                );
                return;
            }
        }

        let published = scene
            .map
            .object_asset_ref(object.id)
            .and_then(|asset_ref| self.placeable_registry.resolve_persistent_ref(asset_ref))
            .or_else(|| self.placeable_registry.for_legacy_object(object.kind));
        if let Some(definition) = published {
            // Current runtime asset loading indexes direct placeable textures by
            // stable_id. Older/alternate pack loaders may use the qualified key.
            // Accept both so a valid published object never keeps collision while
            // silently losing its visual because the cache key shape drifted.
            let texture = self
                .placeable_textures
                .get(definition.pack_qualified_id())
                .or_else(|| self.placeable_textures.get(&definition.stable_id));
            if let (Some(texture), Some(visual)) = (texture, definition.visual.as_ref()) {
                let state = object_state;
                let animation = self.active_scene_door_animation(&scene.id, object.id);
                let resolved_frame = if let Some(animation) = animation {
                    animation
                        .source_rect()
                        .map(|source_rect| (source_rect, animation.draw_offset_px()))
                } else {
                    visual
                        .frame_for_state(state)
                        .map(|frame| (frame.source_rect, frame.draw_offset_px))
                };
                if let Some((source_rect, draw_offset_px)) = resolved_frame {
                    let foot = object_foot_world(object) + offset;
                    let foot = if global_surface {
                        self.runtime_world_to_screen(foot)
                    } else {
                        self.world_to_screen(foot)
                    };
                    draw_texture_ex(
                        texture,
                        foot.x - visual.foot_anchor[0] + draw_offset_px[0],
                        foot.y - visual.foot_anchor[1] + draw_offset_px[1],
                        WHITE,
                        DrawTextureParams {
                            dest_size: Some(vec2(source_rect[2], source_rect[3])),
                            source: Some(Rect::new(
                                source_rect[0],
                                source_rect[1],
                                source_rect[2],
                                source_rect[3],
                            )),
                            ..Default::default()
                        },
                    );
                    return;
                }
            }
        }

        if let (Some(texture), Some(entry)) = (
            &self.object_atlas,
            object_asset_entry_for_cell(object.kind, object.x, object.y),
        ) {
            let foot = object_foot_world(object) + offset;
            let foot = if global_surface {
                self.runtime_world_to_screen(foot)
            } else {
                self.world_to_screen(foot)
            };
            draw_texture_ex(
                texture,
                foot.x - entry.foot_anchor.0,
                foot.y - entry.foot_anchor.1,
                WHITE,
                DrawTextureParams {
                    dest_size: Some(vec2(entry.rect.w, entry.rect.h)),
                    source: Some(atlas_rect(entry.rect)),
                    ..Default::default()
                },
            );
            return;
        }

        if object.kind == ObjectKind::CaveEntrance {
            draw_object_fallback(object, screen_origin);
        }
    }
}
