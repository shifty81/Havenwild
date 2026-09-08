use super::asset_browser_ui::*;
use super::render_helpers::*;
use super::workspace_shell::AssetBrowserScope;
use super::*;
use haven_assets::asset_palette::{AssetPaletteEntry, AssetPaletteKind, AssetPaletteTreeGroup};

const ASSET_TREE_ROW_HEIGHT: f32 = 22.0;

#[derive(Clone, Debug)]
pub(crate) struct AssetPaletteDrag {
    pub stable_id: String,
    pub kind: AssetPaletteKind,
}

impl EditorApp {
    pub(crate) fn draw_asset_palette(&mut self, rect: Rect) {
        draw_section_header(
            Rect::new(rect.x, rect.y, rect.w, 24.0),
            "Asset Browser",
            Some(self.asset_category.label()),
        );
        let search = asset_search_rect(rect);
        draw_editor_widget_tone(
            search,
            if self.asset_filter.is_empty() {
                "Search assets..."
            } else {
                self.asset_filter.as_str()
            },
            self.text_focus == EditorTextFocus::AssetFilter,
            WidgetTone::Quiet,
        );
        draw_editor_widget_tone(
            asset_search_clear_rect(rect),
            "×",
            false,
            if self.asset_filter.is_empty() {
                WidgetTone::Disabled
            } else {
                WidgetTone::Quiet
            },
        );

        for (index, row) in asset_tree_rows(self.asset_category).into_iter().enumerate() {
            let row_rect = asset_tree_row_rect(rect, index);
            match row {
                AssetTreeRow::Group(group, expanded) => {
                    draw_list_row(
                        row_rect,
                        &format!("{} {}", if expanded { "▾" } else { "▸" }, group.label()),
                        Some("Folder"),
                        false,
                    );
                }
                AssetTreeRow::Category(category, depth) => {
                    let label = format!("{}{}", "  ".repeat(depth), category.label());
                    draw_list_row(row_rect, &label, None, category == self.asset_category);
                }
            }
        }
        draw_editor_widget(
            asset_favorites_rect(rect),
            if self.asset_favorites_only {
                "★ Favorites"
            } else {
                "☆ Favorites"
            },
            self.asset_favorites_only,
        );
        draw_editor_widget(asset_recent_rect(rect), "Recent", self.asset_recent_only);

        let entries = self
            .filtered_asset_entries()
            .into_iter()
            .cloned()
            .collect::<Vec<_>>();
        let grid = asset_grid_rect(rect);
        let capacity = browser_visible_capacity(grid).max(1);
        let max_start = entries.len().saturating_sub(capacity);
        self.asset_list_offset = self.asset_list_offset.min(max_start);
        let start = self.asset_list_offset;
        let end = (start + capacity).min(entries.len());

        for (slot, entry) in entries[start..end].iter().enumerate() {
            let card = browser_card_rect(grid, slot);
            let active = self.asset_entry_is_selected(entry);
            draw_browser_card_surface(card, active);
            let thumbnail = browser_thumbnail_rect(card);
            draw_rectangle(
                thumbnail.x,
                thumbnail.y,
                thumbnail.w,
                thumbnail.h,
                Color::new(0.08, 0.09, 0.09, 1.0),
            );
            let mut drew_thumbnail = self.editor_textures.draw_palette_thumbnail(entry, thumbnail);
            if !drew_thumbnail && matches!(entry.kind, AssetPaletteKind::SourceReference) {
                if let Some(sheet) = entry.sheet.as_deref() {
                    let path = haven_assets::asset_intake::repo_root_dir().join(sheet);
                    if !self.unified_asset_browser.contains_or_failed(&entry.stable_id) {
                        let _ = self
                            .unified_asset_browser
                            .load_thumbnail(entry.stable_id.clone(), &path);
                    }
                    if let Some(texture) = self.unified_asset_browser.texture(&entry.stable_id) {
                        draw_browser_texture(texture, thumbnail);
                        drew_thumbnail = true;
                    }
                }
            }
            if !drew_thumbnail {
                draw_thumbnail_placeholder(thumbnail, &entry.label);
            }
            let subtitle = if entry.runtime_ready() {
                format!("Ready · {}", entry.category.label())
            } else if matches!(entry.kind, AssetPaletteKind::SourceReference) {
                "LPC Source · Needs Binding".to_string()
            } else {
                "Needs Binding".to_string()
            };
            draw_browser_card_labels(card, &entry.label, Some(&subtitle));
            if self.asset_palette_state.is_favorite(&entry.stable_id) {
                draw_editor_text("★", card.x + card.w - 18.0, card.y + 18.0, 14.0, GOOD);
            }
        }

        if entries.is_empty() {
            let empty = Rect::new(grid.x, grid.y, grid.w, grid.h.min(132.0));
            draw_rectangle(
                empty.x,
                empty.y,
                empty.w,
                empty.h,
                Color::new(0.05, 0.06, 0.075, 1.0),
            );
            draw_rectangle_lines(empty.x, empty.y, empty.w, empty.h, 1.0, PANEL_EDGE);
            draw_editor_text(
                "No catalog matches",
                empty.x + 14.0,
                empty.y + 34.0,
                18.0,
                TEXT,
            );
            draw_wrapped(
                "Clear search, favorites, recent filters, or select another semantic folder.",
                empty.x + 14.0,
                empty.y + 58.0,
                empty.w - 28.0,
                14.0,
                MUTED,
            );
        }

        draw_asset_scrollbar(grid, start, capacity, entries.len());
        let footer = asset_footer_rect(rect);
        let range = if entries.is_empty() {
            "0".to_string()
        } else {
            format!("{}–{}", start + 1, end)
        };
        draw_scissored_text(
            &format!(
                "{} results · showing {} · scroll to browse",
                entries.len(),
                range
            ),
            footer.x,
            footer.y + 15.0,
            footer.w,
            12.0,
            MUTED,
        );
        let source_count = entries.iter().filter(|entry| matches!(entry.kind, AssetPaletteKind::SourceReference)).count();
        if source_count > 0 {
            draw_editor_widget(
                asset_batch_setup_rect(rect),
                &format!("Batch Setup ({source_count})"),
                false,
            );
        }
        if let Some(stable_id) = self.selected_source_reference.as_deref() {
            draw_scissored_text(
                &format!("Selected source: {stable_id}"),
                footer.x, footer.y + 31.0, (footer.w - 112.0).max(40.0), 10.5, TEXT,
            );
            draw_editor_widget(asset_finish_setup_rect(rect), "Finish Setup", false);
            draw_scissored_text(
                "Creates a reviewed local promotion candidate; source art remains read-only and non-placeable until a real binding passes validation.",
                footer.x, footer.y + 52.0, footer.w, 9.5, MUTED,
            );
        } else {
            draw_scissored_text(
                "Ready cards can be painted/placed. LPC Source cards remain visible and non-placeable until promoted/bound.",
                footer.x, footer.y + 36.0, footer.w, 10.5, TEXT,
            );
        }
    }

    pub(crate) fn handle_asset_palette_click(&mut self, mx: f32, my: f32, rect: Rect) -> bool {
        let mouse = vec2(mx, my);
        if !rect.contains(mouse) {
            return false;
        }
        if asset_batch_setup_rect(rect).contains(mouse) {
            self.status_message = self
                .create_lpc_batch_promotion_candidate()
                .unwrap_or_else(|error| format!("Batch promotion candidate failed: {error}"));
            return true;
        }
        if asset_finish_setup_rect(rect).contains(mouse) {
            if let Some(stable_id) = self.selected_source_reference.clone() {
                self.status_message = self.create_lpc_promotion_candidate(&stable_id)
                    .unwrap_or_else(|error| format!("Promotion candidate failed: {error}"));
            }
            return true;
        }
        if asset_search_rect(rect).contains(mouse) {
            self.text_focus = EditorTextFocus::AssetFilter;
            return true;
        }
        if asset_search_clear_rect(rect).contains(mouse) {
            if !self.asset_filter.is_empty() {
                self.asset_filter.clear();
                self.asset_list_offset = 0;
                self.status_message = "Scene Asset search cleared".to_string();
            }
            return true;
        }
        for (index, row) in asset_tree_rows(self.asset_category).into_iter().enumerate() {
            if !asset_tree_row_rect(rect, index).contains(mouse) {
                continue;
            }
            let category = match row {
                AssetTreeRow::Group(group, _) => group.first_category(),
                AssetTreeRow::Category(category, _) => category,
            };
            self.asset_category = category;
            self.asset_list_offset = 0;
            self.asset_recent_only = false;
            self.status_message = format!("Asset folder: {}", category.label());
            return true;
        }
        if asset_favorites_rect(rect).contains(mouse) {
            self.asset_favorites_only = !self.asset_favorites_only;
            self.asset_list_offset = 0;
            self.status_message = if self.asset_favorites_only {
                "Showing favorite assets".to_string()
            } else {
                "Showing all matching assets".to_string()
            };
            return true;
        }
        if asset_recent_rect(rect).contains(mouse) {
            self.asset_recent_only = !self.asset_recent_only;
            self.asset_list_offset = 0;
            self.status_message = if self.asset_recent_only {
                "Showing recently used assets".to_string()
            } else {
                "Recent asset filter cleared".to_string()
            };
            return true;
        }
        let entries: Vec<(String, AssetPaletteKind, String, bool, Option<String>)> = self
            .filtered_asset_entries()
            .into_iter()
            .map(|entry| {
                (
                    entry.stable_id.clone(),
                    entry.kind,
                    entry.provenance.label().to_string(),
                    entry.runtime_ready(),
                    entry.warning.clone(),
                )
            })
            .collect();
        let grid = asset_grid_rect(rect);
        let capacity = browser_visible_capacity(grid).max(1);
        let start = self
            .asset_list_offset
            .min(entries.len().saturating_sub(capacity));
        for slot in 0..capacity {
            let Some((stable_id, kind, provenance, runtime_ready, warning)) =
                entries.get(start + slot).cloned()
            else {
                break;
            };
            let card = browser_card_rect(grid, slot);
            if asset_favorite_star_rect(card).contains(mouse) {
                let favorite = self.asset_palette_state.toggle_favorite(&stable_id);
                let _ = self.asset_palette_state.save_default();
                self.status_message = format!(
                    "{} {}",
                    if favorite {
                        "Favorited"
                    } else {
                        "Removed favorite"
                    },
                    stable_id
                );
                return true;
            }
            if card.contains(mouse) {
                self.asset_palette_state.mark_recent(&stable_id);
                let _ = self.asset_palette_state.save_default();
                if matches!(kind, AssetPaletteKind::SourceReference) {
                    self.asset_drag = None;
                    self.selected_source_reference = Some(stable_id.clone());
                    self.status_message = warning.unwrap_or_else(|| {
                        format!(
                            "{} is visible from the LPC source catalog and needs semantic/runtime binding before placement",
                            stable_id
                        )
                    });
                    return true;
                }
                self.select_palette_asset(stable_id.clone(), kind);
                self.asset_drag = Some(AssetPaletteDrag { stable_id, kind });
                self.status_message = warning.unwrap_or_else(|| {
                    format!(
                        "Selected palette asset ({provenance}, {}) — drag to canvas or click a cell",
                        if runtime_ready { "runtime ready" } else { "binding warning" }
                    )
                });
                return true;
            }
        }
        true
    }

    pub(crate) fn update_asset_palette_drag(&mut self) {
        if !is_mouse_button_released(MouseButton::Left) {
            return;
        }
        let Some(drag) = self.asset_drag.take() else {
            return;
        };
        match self.viewport_mode {
            EditorViewportMode::SceneMap => {
                let Some((x, y)) = self.scene_cell_at_mouse() else {
                    return;
                };
                self.scene_cursor_x = x;
                self.scene_cursor_y = y;
                self.select_palette_asset(drag.stable_id, drag.kind);
                self.apply_scene_edit_tool();
            }
            EditorViewportMode::SceneRectangles => {
                let Some(cell) = self.world_cell_at_mouse() else {
                    return;
                };
                self.world_cursor_x = cell.x;
                self.world_cursor_y = cell.y;
                self.select_palette_asset(drag.stable_id, drag.kind);
                match drag.kind {
                    AssetPaletteKind::Tile(_) => {
                        self.world_asset_place_anchor = None;
                        self.status_message = format!(
                            "World terrain brush armed at {}, {} | click or drag to paint",
                            cell.x, cell.y
                        );
                    }
                    AssetPaletteKind::Object(_) | AssetPaletteKind::Stamp => {
                        self.arm_world_asset_place_preview(cell);
                    }
                    AssetPaletteKind::SourceReference => {}
                }
            }
            _ => {}
        }
    }

    pub(crate) fn update_asset_palette_scroll_input(&mut self) -> bool {
        if self.workspace_shell.shared_palette_visible
            && self.canvas_supports_shared_palette()
            && self.viewport_mode != EditorViewportMode::PixelStudio
            && self.canvas_authoring_context.brush_mode != super::brush_authoring::BrushMode::Pixel
        {
            let rect = super::shared_palette::shared_palette_rect(self);
            return self.update_canvas_brush_palette_scroll(rect);
        }
        let body = {
            let Some(body) = self.active_asset_browser_body_rect() else {
                return false;
            };
            body
        };
        let palette_visible = self.workspace_shell.asset_browser_scope == AssetBrowserScope::AllProject
            || matches!(
                self.viewport_mode,
                EditorViewportMode::RegionGraph
                    | EditorViewportMode::SceneRectangles
                    | EditorViewportMode::SceneBank
                    | EditorViewportMode::SceneMap
            );
        if !palette_visible {
            return false;
        }
        let point = vec2(mouse_position().0, mouse_position().1);
        let grid = asset_grid_rect(body);
        if !grid.contains(point) {
            return false;
        }
        let wheel = mouse_wheel().1;
        if wheel.abs() <= 0.01 {
            return false;
        }
        let count = self.filtered_asset_entries().len();
        let capacity = browser_visible_capacity(grid).max(1);
        let columns = browser_columns(grid.w).max(1);
        let rows = wheel.abs().ceil().max(1.0) as usize;
        let delta = columns.saturating_mul(rows);
        if wheel < 0.0 {
            self.asset_list_offset = self
                .asset_list_offset
                .saturating_add(delta)
                .min(count.saturating_sub(capacity));
        } else {
            self.asset_list_offset = self.asset_list_offset.saturating_sub(delta);
        }
        true
    }

    pub(crate) fn draw_asset_drag_preview(&self) {
        let Some(drag) = &self.asset_drag else {
            return;
        };
        if !is_mouse_button_down(MouseButton::Left) {
            return;
        }
        let Some(entry) = self.asset_catalog.entry(&drag.stable_id) else {
            return;
        };
        let (mx, my) = mouse_position();
        let rect = Rect::new(mx + 12.0, my + 12.0, 52.0, 52.0);
        draw_rectangle(
            rect.x - 3.0,
            rect.y - 3.0,
            rect.w + 6.0,
            rect.h + 25.0,
            PANEL_BG,
        );
        draw_rectangle_lines(
            rect.x - 3.0,
            rect.y - 3.0,
            rect.w + 6.0,
            rect.h + 25.0,
            1.0,
            PANEL_EDGE,
        );
        if !self.editor_textures.draw_palette_thumbnail(entry, rect) {
            draw_editor_text("!", rect.x + 18.0, rect.y + 34.0, 28.0, WARN);
        }
        draw_scissored_text(&entry.label, rect.x, rect.y + 70.0, rect.w, 13.0, TEXT);
    }

    fn create_lpc_promotion_candidate(&self, stable_id: &str) -> Result<String, String> {
        let entry = self.asset_catalog.entry(stable_id)
            .ok_or_else(|| format!("unknown source reference {stable_id}"))?;
        if !matches!(entry.kind, AssetPaletteKind::SourceReference) {
            return Err(format!("{stable_id} is not an LPC source reference"));
        }
        let source_path = entry.sheet.clone().ok_or_else(|| "source reference has no mounted source path".to_string())?;
        let root = haven_assets::asset_intake::repo_root_dir();
        let directory = root.join(".local/editor/lpc_promotion_candidates");
        std::fs::create_dir_all(&directory)
            .map_err(|error| format!("failed to create {}: {error}", directory.display()))?;
        let filename = stable_id.chars()
            .map(|ch| if ch.is_ascii_alphanumeric() || ch == '-' || ch == '_' { ch } else { '_' })
            .collect::<String>();
        let path = directory.join(format!("{filename}.json"));
        let payload = serde_json::json!({
            "schema": "havenwild.editor.lpc_promotion_candidate.r30.v1",
            "stableId": entry.stable_id.clone(),
            "displayName": entry.label.clone(),
            "semanticCategory": entry.category.label(),
            "sourcePath": source_path,
            "provenance": entry.provenance.label(),
            "state": "cataloged",
            "sourceReadOnly": true,
            "runtimePlaceable": false,
            "requiredReview": [
                "semantic_type",
                "license_provenance",
                "placement_footprint",
                "collision_profile",
                "interaction_profile",
                "animation_profile"
            ],
            "promotionRule": "A promotion candidate is review metadata only. Copy/derive into a governed project asset and validate a runtime binding before production use."
        });
        let text = serde_json::to_string_pretty(&payload)
            .map_err(|error| format!("failed to encode promotion candidate: {error}"))?;
        std::fs::write(&path, format!("{text}\\n"))
            .map_err(|error| format!("failed to write {}: {error}", path.display()))?;
        Ok(format!("Created LPC promotion candidate: {} · source remains read-only", path.display()))
    }

    fn create_lpc_batch_promotion_candidate(&self) -> Result<String, String> {
        let sources = self
            .filtered_asset_entries()
            .into_iter()
            .filter(|entry| matches!(entry.kind, AssetPaletteKind::SourceReference))
            .map(|entry| serde_json::json!({
                "stableId": entry.stable_id.clone(),
                "displayName": entry.label.clone(),
                "semanticCategory": entry.category.label(),
                "sourcePath": entry.sheet.clone(),
                "runtimePlaceable": false,
            }))
            .collect::<Vec<_>>();
        if sources.is_empty() {
            return Err("the current Asset Browser scope contains no LPC source references".to_string());
        }
        let source_count = sources.len();
        let root = haven_assets::asset_intake::repo_root_dir();
        let directory = root.join(".local/editor/lpc_promotion_batches");
        std::fs::create_dir_all(&directory)
            .map_err(|error| format!("failed to create {}: {error}", directory.display()))?;
        let category = self.asset_category.label();
        let stem = category
            .chars()
            .map(|ch| if ch.is_ascii_alphanumeric() { ch.to_ascii_lowercase() } else { '_' })
            .collect::<String>();
        let path = directory.join(format!("{stem}_batch.json"));
        let payload = serde_json::json!({
            "schema": "havenwild.editor.lpc_promotion_batch.r30.v1",
            "category": category,
            "search": self.asset_filter,
            "sourceCount": source_count,
            "sources": sources,
            "state": "review_required",
            "sourceReadOnly": true,
            "runtimePlaceable": false,
            "batchWorkflow": [
                "verify_license_provenance",
                "confirm_semantic_family",
                "detect_shared_footprint_animation_interaction_rules",
                "preview_exceptions",
                "promote_passing_members",
                "route_exceptions_to_manual_finish_setup"
            ],
            "rule": "Batch review creates governed bindings/derivatives only after validation; no upstream LPC source is mutated."
        });
        let text = serde_json::to_string_pretty(&payload)
            .map_err(|error| format!("failed to encode LPC promotion batch: {error}"))?;
        std::fs::write(&path, format!("{text}\n"))
            .map_err(|error| format!("failed to write {}: {error}", path.display()))?;
        Ok(format!(
            "Queued {} LPC source references for batch setup: {}",
            source_count,
            path.display(),
        ))
    }

    fn filtered_asset_entries(&self) -> Vec<&AssetPaletteEntry> {
        let mut entries = self.asset_catalog.filtered(
            self.asset_category,
            &self.asset_filter,
            self.asset_favorites_only,
            &self.asset_palette_state,
        );
        if self.asset_recent_only {
            entries.retain(|entry| self.asset_palette_state.recent().contains(&entry.stable_id));
            entries.sort_by_key(|entry| {
                self.asset_palette_state
                    .recent()
                    .iter()
                    .position(|stable_id| stable_id == &entry.stable_id)
                    .unwrap_or(usize::MAX)
            });
        }
        entries
    }

    pub(crate) fn select_palette_asset(&mut self, stable_id: String, kind: AssetPaletteKind) {
        if let Some((compatibility_kind, definition_label)) = self
            .placeable_registry
            .entry(&stable_id)
            .map(|definition| (definition.compatibility_kind(), definition.label.clone()))
        {
            self.selected_source_reference = None;
            self.selected_stamp_id = None;
            self.selected_placeable_id = Some(stable_id.clone());
            self.selected_placeable_preview_state = 0;
            if let Some(index) = OBJECT_BRUSHES
                .iter()
                .position(|candidate| *candidate == compatibility_kind)
            {
                self.selected_object = index;
            }
            if self.viewport_mode == EditorViewportMode::SceneRectangles {
                self.world_layer_mode = WorldLayerMode::Objects;
            } else {
                self.scene_layer_mode = SceneLayerMode::Objects;
            }
            self.asset_palette_state.mark_recent(&stable_id);
            let _ = self.asset_palette_state.save_default();
            self.canvas_authoring_context.source_id = Some(stable_id.clone());
            self.sync_canvas_authoring_context();
            self.status_message = format!(
                "Selected published asset {} · exact id {}",
                definition_label, stable_id
            );
            return;
        }
        if !matches!(kind, AssetPaletteKind::SourceReference) {
            self.selected_source_reference = None;
        }
        match kind {
            AssetPaletteKind::Tile(tile) => {
                self.selected_stamp_id = None;
                self.selected_placeable_id = None;
                if let Some(index) = TileKind::ALL
                    .iter()
                    .position(|candidate| *candidate == tile)
                {
                    self.selected_tile = index;
                }
                if self.viewport_mode == EditorViewportMode::SceneRectangles {
                    self.world_layer_mode = WorldLayerMode::Terrain;
                    self.world_asset_place_anchor = None;
                } else {
                    self.scene_layer_mode = SceneLayerMode::Terrain;
                }
            }
            AssetPaletteKind::Object(object) => {
                self.selected_stamp_id = None;
                self.selected_placeable_id = None;
                if let Some(index) = OBJECT_BRUSHES
                    .iter()
                    .position(|candidate| *candidate == object)
                {
                    self.selected_object = index;
                }
                if self.viewport_mode == EditorViewportMode::SceneRectangles {
                    self.world_layer_mode = WorldLayerMode::Objects;
                } else {
                    self.scene_layer_mode = SceneLayerMode::Objects;
                }
            }
            AssetPaletteKind::Stamp => {
                self.selected_stamp_id = stable_id.strip_prefix("stamp/").map(str::to_string);
                self.selected_placeable_id = None;
                if self.viewport_mode == EditorViewportMode::SceneRectangles {
                    self.world_layer_mode = WorldLayerMode::Objects;
                } else {
                    self.scene_layer_mode = SceneLayerMode::Objects;
                }
            }
            AssetPaletteKind::SourceReference => return,
        }
        self.asset_palette_state.mark_recent(&stable_id);
        let _ = self.asset_palette_state.save_default();
        self.canvas_authoring_context.source_id = Some(stable_id);
        self.sync_canvas_authoring_context();
    }

    pub(crate) fn asset_entry_is_selected(&self, entry: &AssetPaletteEntry) -> bool {
        if self.selected_placeable_id.as_deref() == Some(entry.stable_id.as_str()) {
            return true;
        }
        let world = self.viewport_mode == EditorViewportMode::SceneRectangles;
        match entry.kind {
            AssetPaletteKind::Tile(tile) => {
                (if world {
                    self.world_layer_mode == WorldLayerMode::Terrain
                } else {
                    self.scene_layer_mode == SceneLayerMode::Terrain
                }) && self.selected_tile_kind() == tile
            }
            AssetPaletteKind::Object(object) => {
                (if world {
                    self.world_layer_mode == WorldLayerMode::Objects
                } else {
                    self.scene_layer_mode == SceneLayerMode::Objects
                }) && self.selected_stamp_id.is_none()
                    && self.selected_placeable_id.is_none()
                    && self.selected_object_kind() == object
            }
            AssetPaletteKind::Stamp => {
                (if world {
                    self.world_layer_mode == WorldLayerMode::Objects
                } else {
                    self.scene_layer_mode == SceneLayerMode::Objects
                }) && self
                    .selected_stamp_id
                    .as_deref()
                    .is_some_and(|id| entry.stable_id == format!("stamp/{id}"))
            }
            AssetPaletteKind::SourceReference => self.selected_source_reference.as_deref() == Some(entry.stable_id.as_str()),
        }
    }

}

fn asset_search_rect(rect: Rect) -> Rect {
    Rect::new(rect.x, rect.y + 32.0, (rect.w - 30.0).max(40.0), 24.0)
}

fn asset_search_clear_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + rect.w - 24.0, rect.y + 32.0, 24.0, 24.0)
}

#[derive(Clone, Copy, Debug)]
enum AssetTreeRow {
    Group(AssetPaletteTreeGroup, bool),
    Category(AssetPaletteCategory, usize),
}

fn asset_tree_rows(active: AssetPaletteCategory) -> Vec<AssetTreeRow> {
    let active_group = active
        .tree_group()
        .unwrap_or(AssetPaletteTreeGroup::Terrain);
    let mut rows = vec![AssetTreeRow::Category(AssetPaletteCategory::All, 0)];
    for group in AssetPaletteTreeGroup::ALL {
        let expanded = group == active_group;
        rows.push(AssetTreeRow::Group(group, expanded));
        if expanded {
            rows.extend(
                AssetPaletteCategory::children(group)
                    .iter()
                    .copied()
                    .map(|category| AssetTreeRow::Category(category, 1)),
            );
        }
    }
    rows.push(AssetTreeRow::Category(AssetPaletteCategory::Stamps, 0));
    rows
}

fn asset_tree_row_rect(rect: Rect, index: usize) -> Rect {
    Rect::new(
        rect.x,
        rect.y + 62.0 + index as f32 * ASSET_TREE_ROW_HEIGHT,
        rect.w,
        ASSET_TREE_ROW_HEIGHT - 2.0,
    )
}

fn asset_tree_bottom(rect: Rect) -> f32 {
    let max_children = AssetPaletteTreeGroup::ALL
        .iter()
        .map(|group| AssetPaletteCategory::children(*group).len())
        .max()
        .unwrap_or(0);
    let max_tree_rows = 1 + AssetPaletteTreeGroup::ALL.len() + max_children + 1;
    rect.y + 62.0 + max_tree_rows as f32 * ASSET_TREE_ROW_HEIGHT
}

fn asset_favorites_rect(rect: Rect) -> Rect {
    Rect::new(
        rect.x,
        asset_tree_bottom(rect) + 5.0,
        (rect.w - 5.0) * 0.5,
        28.0,
    )
}

fn asset_recent_rect(rect: Rect) -> Rect {
    let favorite = asset_favorites_rect(rect);
    Rect::new(
        favorite.x + favorite.w + 5.0,
        favorite.y,
        favorite.w,
        favorite.h,
    )
}

fn asset_footer_rect(rect: Rect) -> Rect {
    Rect::new(rect.x, (rect.y + rect.h - 70.0).max(rect.y), rect.w, 70.0)
}

fn asset_batch_setup_rect(rect: Rect) -> Rect {
    let footer = asset_footer_rect(rect);
    Rect::new(footer.x + footer.w - 230.0, footer.y + 22.0, 116.0, 24.0)
}

fn asset_finish_setup_rect(rect: Rect) -> Rect {
    let footer = asset_footer_rect(rect);
    Rect::new(footer.x + footer.w - 108.0, footer.y + 22.0, 108.0, 24.0)
}

fn asset_grid_rect(rect: Rect) -> Rect {
    let top = asset_favorites_rect(rect).y + 36.0;
    let footer = asset_footer_rect(rect);
    Rect::new(rect.x, top, rect.w, (footer.y - top - 4.0).max(BROWSER_CARD_H))
}

fn asset_favorite_star_rect(card: Rect) -> Rect {
    Rect::new(card.x + card.w - 28.0, card.y, 28.0, 24.0)
}

fn draw_asset_scrollbar(grid: Rect, start: usize, capacity: usize, total: usize) {
    if total <= capacity || total == 0 {
        return;
    }
    let track = Rect::new(grid.x + grid.w - 3.0, grid.y, 3.0, grid.h);
    draw_rectangle(track.x, track.y, track.w, track.h, Color::new(0.12, 0.13, 0.15, 0.85));
    let fraction = (capacity as f32 / total as f32).clamp(0.06, 1.0);
    let thumb_h = (track.h * fraction).max(18.0).min(track.h);
    let max_start = total.saturating_sub(capacity).max(1);
    let progress = (start.min(max_start) as f32 / max_start as f32).clamp(0.0, 1.0);
    let thumb_y = track.y + (track.h - thumb_h) * progress;
    draw_rectangle(track.x, thumb_y, track.w, thumb_h, editor_theme::colors::ACCENT);
}

