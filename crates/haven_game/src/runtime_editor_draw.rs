use super::*;

impl Game {
    pub(super) fn draw_editor_cursor(&self) {
        if !self.dev_mode || !self.build_mode {
            return;
        }
        let (mx, my) = mouse_position();
        let Some(target) = self.surface_cell_target_at_screen(vec2(mx, my)) else {
            return;
        };
        let tx = target.local_x;
        let ty = target.local_y;
        let half = self.brush_size / 2;
        let (screen, width_tiles, height_tiles) = if self.world.active().kind == SceneKind::Exterior
        {
            let min_global_x = target.global_x - half;
            let min_global_y = target.global_y - half;
            (
                self.runtime_world_to_screen(vec2(
                    min_global_x as f32 * TILE_SIZE,
                    min_global_y as f32 * TILE_SIZE,
                )),
                self.brush_size.max(1),
                self.brush_size.max(1),
            )
        } else {
            let min_x = self.brush_min(tx);
            let min_y = self.brush_min(ty);
            let dimensions = self.world.active().dimensions;
            let max_x = self.brush_max(tx, dimensions.width as i32);
            let max_y = self.brush_max(ty, dimensions.height as i32);
            (
                self.world_to_screen(vec2(min_x as f32 * TILE_SIZE, min_y as f32 * TILE_SIZE)),
                max_x - min_x + 1,
                max_y - min_y + 1,
            )
        };
        draw_rectangle_lines(
            screen.x,
            screen.y,
            width_tiles as f32 * TILE_SIZE,
            height_tiles as f32 * TILE_SIZE,
            3.0,
            Color::from_rgba(255, 238, 151, 255),
        );
        if let BuildTool::Object(kind) = self.palette.tools[self.selected_tool] {
            if &target.scene_id != self.world.active_scene.project_id() {
                let text_origin = self.surface_cell_screen_origin(&target);
                draw_text(
                    "Cross-partition F3 editing is terrain-only in this pass",
                    text_origin.x + 4.0,
                    text_origin.y - 8.0,
                    15.0,
                    Color::from_rgba(255, 209, 120, 255),
                );
                return;
            }
            let selected = self
                .placeable_registry
                .entries()
                .get(self.selected_placeable_index);
            let preview = if let Some(definition) = selected {
                PlacedObject::with_footprint(
                    definition.compatibility_kind(),
                    tx,
                    ty,
                    definition.footprint,
                )
            } else {
                let mut preview = PlacedObject::new(kind, tx, ty);
                preview.footprint = audited_object_footprint_for_cell(kind, tx, ty);
                preview
            };
            let issues = self.world.active().map.placement_issues_for_object(preview);
            let valid = issues.is_empty();
            self.draw_object_footprint_preview(preview, valid);
            let label = if valid { "valid" } else { "blocked" };
            let text_origin =
                self.world_to_screen(vec2(tx as f32 * TILE_SIZE, ty as f32 * TILE_SIZE));
            draw_text(
                &format!(
                    "{} {}",
                    selected.map_or(kind.label(), |definition| definition.label.as_str()),
                    label
                ),
                text_origin.x + 4.0,
                text_origin.y - 8.0,
                15.0,
                if valid {
                    Color::from_rgba(160, 244, 162, 255)
                } else {
                    Color::from_rgba(255, 128, 128, 255)
                },
            );
        }
    }

    pub(super) fn draw_editor_footprint_overlays(&self) {
        if !self.dev_mode || !self.build_mode {
            return;
        }
        let scene = self.world.active();
        let map = &scene.map;
        if !self.show_footprint_overlay
            && !self.show_collision_overlay
            && !self.show_interaction_overlay
            && self.selected_object_index.is_none()
        {
            return;
        }

        if self.show_collision_overlay {
            if self.world.active().kind == SceneKind::Exterior {
                // Never scan/draw an entire 96x96 storage partition in F3. At
                // ocean-heavy spawns that submitted thousands of off-screen red
                // rectangles every frame and collapsed editor mode to ~1 FPS.
                let viewport = vec2(screen_width().max(1.0), screen_height().max(1.0));
                let half_visible = viewport / self.camera_zoom.max(0.01) * 0.5;
                let min_x = ((self.camera_target.x - half_visible.x) / TILE_SIZE).floor() as i32 - 2;
                let min_y = ((self.camera_target.y - half_visible.y) / TILE_SIZE).floor() as i32 - 2;
                let max_x = ((self.camera_target.x + half_visible.x) / TILE_SIZE).ceil() as i32 + 2;
                let max_y = ((self.camera_target.y + half_visible.y) / TILE_SIZE).ceil() as i32 + 2;
                let manifest = haven_world::ContinuousSurfaceManifest::for_world(&self.world);
                // Resolve chunk -> scene once per frame. The previous overlay
                // path performed a world scene lookup for every visible tile;
                // with dozens of streamed partitions that turned F3 collision
                // visualization into an O(visible-cells * loaded-scenes) scan.
                let scenes_by_chunk = manifest
                    .exterior_bindings
                    .iter()
                    .filter_map(|binding| {
                        self.world
                            .scene_by_id(&binding.scene_id)
                            .map(|scene| (binding.chunk, scene))
                    })
                    .collect::<std::collections::BTreeMap<_, _>>();
                for global_y in min_y..=max_y {
                    for global_x in min_x..=max_x {
                        let address = haven_world::surface_tile_address(
                            haven_world::open_world::WorldTileCoord::new(global_x, global_y),
                        );
                        let Some(surface_scene) = scenes_by_chunk.get(&address.chunk).copied() else {
                            continue;
                        };
                        if surface_scene.is_cell_walkable(address.local_x, address.local_y) {
                            continue;
                        }
                        let screen = self.runtime_world_to_screen(vec2(
                            global_x as f32 * TILE_SIZE,
                            global_y as f32 * TILE_SIZE,
                        ));
                        draw_rectangle(
                            screen.x + 8.0,
                            screen.y + 8.0,
                            TILE_SIZE - 16.0,
                            TILE_SIZE - 16.0,
                            Color::from_rgba(255, 86, 86, 68),
                        );
                    }
                }
            } else {
                let (min_x, min_y, max_x, max_y) = runtime_view_culling::visible_tile_bounds(
                    self.active_local_camera_target(),
                    self.camera_zoom,
                    2,
                    self.world.active().dimensions,
                );
                for y in min_y.max(0)..=max_y.min(self.world.active().dimensions.height as i32 - 1) {
                    for x in min_x.max(0)..=max_x.min(self.world.active().dimensions.width as i32 - 1) {
                        if !scene.is_cell_walkable(x, y) {
                            let screen = self
                                .world_to_screen(vec2(x as f32 * TILE_SIZE, y as f32 * TILE_SIZE));
                            draw_rectangle(
                                screen.x + 8.0,
                                screen.y + 8.0,
                                TILE_SIZE - 16.0,
                                TILE_SIZE - 16.0,
                                Color::from_rgba(255, 86, 86, 68),
                            );
                        }
                    }
                }
            }
        }

        if self.show_interaction_overlay {
            for transition in &scene.transitions {
                self.draw_tile_rect_lines(
                    (transition.x, transition.y, transition.w, transition.h),
                    Color::from_rgba(116, 221, 255, 210),
                    2.0,
                );
            }
        }

        // Object metadata can be numerous in generated exterior chunks. Only
        // submit overlays for objects whose visual/collision/interaction area
        // intersects the current view instead of walking every off-screen prop.
        let visible_object_bounds = runtime_view_culling::visible_tile_bounds(
            self.active_local_camera_target(),
            self.camera_zoom,
            2,
            self.world.active().dimensions,
        );
        for (index, object) in map.objects.iter().enumerate() {
            let visible = runtime_view_culling::tile_rect_intersects_bounds(
                object.visual_rect(),
                visible_object_bounds,
                2,
            ) || runtime_view_culling::tile_rect_intersects_bounds(
                object.collision_rect(),
                visible_object_bounds,
                2,
            ) || runtime_view_culling::tile_rect_intersects_bounds(
                object.interaction_rect(),
                visible_object_bounds,
                2,
            );
            if !visible && Some(index) != self.selected_object_index {
                continue;
            }
            if self.show_footprint_overlay {
                self.draw_tile_rect_lines(
                    object.visual_rect(),
                    Color::from_rgba(120, 178, 255, 210),
                    2.0,
                );
            }
            if self.show_collision_overlay {
                self.draw_tile_rect_lines(
                    object.collision_rect(),
                    Color::from_rgba(255, 86, 86, 230),
                    2.5,
                );
            }
            if self.show_interaction_overlay {
                self.draw_tile_rect_lines(
                    object.interaction_rect(),
                    Color::from_rgba(255, 225, 104, 230),
                    2.0,
                );
            }
            if Some(index) == self.selected_object_index {
                self.draw_tile_rect_lines(
                    object.visual_rect(),
                    Color::from_rgba(255, 255, 255, 255),
                    3.0,
                );
                self.draw_tile_rect_lines(
                    object.collision_rect(),
                    Color::from_rgba(255, 232, 144, 255),
                    3.0,
                );
            }
        }
    }
    pub(super) fn draw_ui(&self) {
        use crate::runtime_ui_theme::{
            draw_runtime_panel, fit_runtime_label, ui_brass_bright, ui_muted, ui_parchment, ui_teal,
        };

        if self.dev_mode {
            let width = (screen_width() - 28.0).min(1080.0).max(420.0);
            let panel = Rect::new(14.0, 14.0, width, 94.0);
            draw_runtime_panel(panel, "DEVELOPMENT", Some("Runtime diagnostics · F3 toggles authoring mode"));
            let state = format!(
                "{} · {} · {} coin · Rep {} · {} FPS · {}",
                self.world.active().name,
                clock_label(self.day_clock),
                self.coin,
                self.reputation,
                get_fps(),
                if self.build_mode { "AUTHORING" } else { "PLAY TEST" },
            );
            draw_text(
                &fit_runtime_label(&state, panel.w - 36.0, 14),
                panel.x + 18.0,
                panel.y + 70.0,
                14.0,
                ui_parchment(),
            );
            let telemetry = self.surface_streaming_telemetry();
            draw_text(
                &fit_runtime_label(&telemetry, panel.w - 36.0, 12),
                panel.x + 18.0,
                panel.y + 88.0,
                12.0,
                ui_teal(),
            );
            if !self.status_message.trim().is_empty() {
                let status = fit_runtime_label(&self.status_message, (screen_width() - 40.0).min(720.0), 13);
                let status_w = measure_text(&status, None, 13, 1.0).width + 24.0;
                draw_rectangle(14.0, 116.0, status_w, 28.0, Color::from_rgba(28, 31, 27, 238));
                draw_rectangle_lines(14.0, 116.0, status_w, 28.0, 1.0, ui_brass_bright());
                draw_text(&status, 26.0, 135.0, 13.0, ui_muted());
            }
        } else if !self.status_message.trim().is_empty() {
            let status = fit_runtime_label(&self.status_message, (screen_width() - 48.0).min(680.0), 13);
            let status_w = measure_text(&status, None, 13, 1.0).width + 28.0;
            let x = (screen_width() - status_w) * 0.5;
            let y = screen_height() - 150.0;
            draw_rectangle(x, y, status_w, 30.0, Color::from_rgba(24, 27, 24, 238));
            draw_rectangle_lines(x, y, status_w, 30.0, 1.0, ui_brass_bright());
            draw_text(&status, x + 14.0, y + 20.0, 13.0, ui_parchment());
        }

        if self.layout_edit_mode {
            let hud = self.panel_rect(UiPanelId::Hud);
            draw_text(
                "Layout Edit: drag panel headers, snap to 16px grid, press L to finish",
                hud.x + 18.0,
                hud.y + 152.0,
                16.0,
                Color::from_rgba(255, 232, 144, 255),
            );
        }

        if self.dev_mode && self.build_mode {
            let rect = self.panel_rect(UiPanelId::Editor);
            draw_panel(rect.x, rect.y, rect.w, rect.h, "Havenwild World Editor");
            let panel_x = rect.x;
            let panel_y = rect.y;
            let tab_w = 68.0;
            let tab_step = 69.0;
            for (i, tab) in EditorTab::ALL.iter().enumerate() {
                let x = panel_x + 12.0 + i as f32 * tab_step;
                let active = *tab == self.editor_tab;
                draw_rectangle(
                    x,
                    panel_y + 42.0,
                    tab_w,
                    26.0,
                    if active {
                        Color::from_rgba(76, 101, 78, 245)
                    } else {
                        Color::from_rgba(31, 45, 49, 230)
                    },
                );
                draw_rectangle_lines(
                    x,
                    panel_y + 42.0,
                    tab_w,
                    26.0,
                    1.0,
                    Color::from_rgba(136, 158, 148, 255),
                );
                draw_text(
                    tab.label(),
                    x + 6.0,
                    panel_y + 60.0,
                    15.0,
                    if active {
                        Color::from_rgba(255, 232, 144, 255)
                    } else {
                        Color::from_rgba(220, 231, 236, 255)
                    },
                );
            }
            if self.editor_tab == EditorTab::World {
                self.draw_world_editor_tab(panel_x);
            } else if self.editor_tab == EditorTab::Objects {
                self.draw_objects_editor_tab(panel_x);
            } else if self.editor_tab == EditorTab::Rules {
                self.draw_rules_editor_tab(panel_x);
            } else if self.editor_tab == EditorTab::Map {
                self.draw_map_editor_tab(panel_x);
            } else if self.editor_tab == EditorTab::Paint {
                self.draw_world_paint_editor_tab(panel_x);
            } else if self.editor_tab == EditorTab::Transitions {
                self.draw_transition_rules_editor_tab(panel_x);
            } else if self.editor_tab == EditorTab::Assets {
                self.draw_asset_reference_browser_tab(panel_x);
            } else {
                self.draw_tool_editor_tab(panel_x);
            }
            draw_line(
                rect.x + rect.w - 16.0,
                rect.y + rect.h - 4.0,
                rect.x + rect.w - 4.0,
                rect.y + rect.h - 16.0,
                2.0,
                Color::from_rgba(136, 158, 148, 255),
            );
            draw_line(
                rect.x + rect.w - 10.0,
                rect.y + rect.h - 4.0,
                rect.x + rect.w - 4.0,
                rect.y + rect.h - 10.0,
                2.0,
                Color::from_rgba(233, 218, 157, 220),
            );
        }
    }

    pub(super) fn draw_tool_editor_tab(&self, panel_x: f32) {
        let rect = self.panel_rect(UiPanelId::Editor);
        let visible_tools = self.visible_tool_indices();
        let start = self.tool_page * 10;
        let end = (start + 10).min(visible_tools.len());
        let panel_y = self.panel_rect(UiPanelId::Editor).y;
        for (slot, visible_index) in (start..end).enumerate() {
            let tool_index = visible_tools[visible_index];
            let tool = self.palette.tools[tool_index];
            let column = slot % 2;
            let row = slot / 2;
            let gap = 14.0;
            let card_w = ((rect.w - 36.0 - gap) * 0.5).max(250.0);
            let x = panel_x + 18.0 + column as f32 * (card_w + gap);
            let y = panel_y + 84.0 + row as f32 * 62.0;
            let label = match tool {
                BuildTool::Floor(tile) if tile.is_lpc_mapped_editor_terrain() => {
                    let badge = match tile.authoring_status() {
                        haven_core::TileAuthoringStatus::LpcProduction => "V7",
                        haven_core::TileAuthoringStatus::DerivedSystem => "derived",
                        haven_core::TileAuthoringStatus::ObjectOrOverlay => "overlay",
                        _ => "mapping",
                    };
                    format!("{}  [{}]", tile.label(), badge)
                }
                _ => tool.label().to_string(),
            };
            draw_rectangle(x, y, card_w, 54.0, Color::from_rgba(25, 40, 43, 242));
            draw_rectangle_lines(
                x,
                y,
                card_w,
                54.0,
                1.0,
                Color::from_rgba(103, 124, 118, 255),
            );
            let text_x =
                if let (EditorTab::Tiles, BuildTool::Floor(_tile), Some(texture), Some(entry)) = (
                    self.editor_tab,
                    tool,
                    self.lpc_mapped_terrain_atlas.as_ref(),
                    match tool {
                        BuildTool::Floor(tile) => lpc_mapped_terrain_preview_entry(tile),
                        _ => None,
                    },
                ) {
                    draw_texture_ex(
                        texture,
                        x + 4.0,
                        y + 4.0,
                        WHITE,
                        DrawTextureParams {
                            dest_size: Some(vec2(46.0, 46.0)),
                            source: Some(atlas_rect(entry.rect)),
                            ..Default::default()
                        },
                    );
                    x + 58.0
                } else {
                    x + 10.0
                };
            draw_text(
                &label,
                text_x,
                y + 32.0,
                16.0,
                Color::from_rgba(220, 231, 236, 255),
            );
            let color = if tool_index == self.selected_tool {
                Color::from_rgba(255, 232, 144, 255)
            } else {
                Color::from_rgba(220, 231, 236, 255)
            };
            if tool_index == self.selected_tool {
                draw_rectangle_lines(x - 2.0, y - 2.0, card_w + 4.0, 58.0, 3.0, color);
            }
        }
        if self.editor_tab == EditorTab::Tiles {
            for (index, mode) in TerrainPaintMode::ALL.into_iter().enumerate() {
                let button = self.terrain_paint_mode_button_rect(index);
                draw_rectangle(
                    button.x,
                    button.y,
                    button.w,
                    button.h,
                    if mode == self.terrain_paint_mode {
                        Color::from_rgba(64, 91, 72, 255)
                    } else {
                        Color::from_rgba(25, 40, 43, 242)
                    },
                );
                draw_rectangle_lines(
                    button.x,
                    button.y,
                    button.w,
                    button.h,
                    if mode == self.terrain_paint_mode {
                        2.0
                    } else {
                        1.0
                    },
                    if mode == self.terrain_paint_mode {
                        Color::from_rgba(255, 232, 144, 255)
                    } else {
                        Color::from_rgba(103, 124, 118, 255)
                    },
                );
                draw_text(
                    mode.label(),
                    button.x + 10.0,
                    button.y + 19.0,
                    15.0,
                    Color::from_rgba(220, 231, 236, 255),
                );
            }
        }
        let context = match self.editor_tab {
            EditorTab::Tiles => format!(
                "Paint {} · {}",
                self.terrain_paint_mode.label(),
                self.terrain_paint_mode.help()
            ),
            EditorTab::Zones => {
                "Gameplay zones · paint permissions and simulation areas".to_string()
            }
            _ => format!(
                "Page {}/{} · Brush {}",
                self.tool_page + 1,
                self.max_tool_page() + 1,
                self.brush_size
            ),
        };
        draw_text(
            &context,
            panel_x + 26.0,
            panel_y + 446.0,
            15.0,
            Color::from_rgba(162, 228, 255, 255),
        );
        draw_text(
            "Q/E tabs  Z/X pages  Ctrl+Z/Y undo/redo",
            panel_x + 26.0,
            panel_y + 466.0,
            14.0,
            Color::from_rgba(208, 224, 232, 255),
        );
        draw_text(
            "Click a tool, then click/drag directly on the map. -/+ changes brush size.",
            panel_x + 26.0,
            panel_y + 484.0,
            14.0,
            Color::from_rgba(208, 224, 232, 255),
        );
        draw_text(
            &format!(
                "Overlay H:{} C:{} I:{} T:{}",
                self.show_footprint_overlay as u8,
                self.show_collision_overlay as u8,
                self.show_interaction_overlay as u8,
                self.show_terrain_debug_overlay as u8
            ),
            panel_x + 26.0,
            panel_y + 502.0,
            13.0,
            Color::from_rgba(162, 228, 255, 255),
        );
    }
}
