use super::asset_browser_ui::*;
use super::pixel_studio_layout::*;
use super::render_helpers::*;
use super::*;

impl EditorApp {
    pub(crate) fn draw_pixel_library(&self, rect: Rect) {
        let filtered = self.pixel_studio.filtered_library_indices();
        let summary = format!(
            "Pixel • {} / {} • {}",
            filtered.len(),
            self.pixel_studio.library.len(),
            self.unified_asset_browser.summary()
        );
        draw_section_header(Rect::new(rect.x, rect.y, rect.w, 24.0), "Asset Browser", Some(&summary));
        draw_editor_widget(pixel_refresh_rect(rect), "Rescan", false);

        let search = pixel_library_search_rect(rect);
        draw_editor_widget_tone(
            search,
            if self.pixel_studio.library_filter.is_empty() { "Search assets..." } else { self.pixel_studio.library_filter.as_str() },
            self.text_focus == EditorTextFocus::PixelLibraryFilter,
            WidgetTone::Quiet,
        );
        draw_editor_widget_tone(
            pixel_library_clear_rect(rect),
            "×",
            false,
            if self.pixel_studio.library_filter.is_empty() { WidgetTone::Disabled } else { WidgetTone::Quiet },
        );
        let category = self
            .pixel_studio
            .active_library_category()
            .map(|value| value.label())
            .unwrap_or("All");
        draw_editor_widget_tone(
            pixel_library_category_rect(rect),
            &format!("Category: {category}"),
            false,
            WidgetTone::Quiet,
        );

        if self.pixel_studio.library.is_empty() {
            let message = if self.pixel_studio.library_loaded {
                "No project images match the active library roots. Use Rescan after adding project-owned content."
            } else {
                "Press Rescan to populate the project asset browser. Assets are shown as thumbnail cards instead of a text-only list."
            };
            draw_wrapped(message, rect.x, rect.y + 112.0, rect.w, 14.5, MUTED);
            return;
        }
        if filtered.is_empty() {
            draw_wrapped("No Pixel Assets match this search.", rect.x, rect.y + 112.0, rect.w, 14.0, MUTED);
            return;
        }

        let grid = pixel_library_grid_rect(rect);
        let capacity = browser_visible_capacity(grid);
        let start = self.pixel_studio.library_offset.min(filtered.len().saturating_sub(1));
        for (slot, &index) in filtered.iter().skip(start).take(capacity).enumerate() {
            let Some(entry) = self.pixel_studio.library.get(index) else { continue; };
            let card = browser_card_rect(grid, slot);
            let subtitle = if entry.recent_rank.is_some() {
                format!("Recent • {} • {}", entry.category.label(), entry.source.label())
            } else {
                format!("{} • {}", entry.category.label(), entry.source.label())
            };
            draw_browser_card_surface(card, index == self.pixel_studio.selected_entry);
            let thumb = browser_thumbnail_rect(card);
            draw_browser_checkerboard(thumb, 8.0);
            if let Some(texture) = self.unified_asset_browser.texture(&entry.relative_path) {
                draw_browser_texture(texture, thumb);
            } else {
                draw_thumbnail_placeholder(thumb, &entry.display_name);
            }
            draw_browser_card_labels(card, &entry.display_name, Some(&subtitle));
        }
    }

    pub(crate) fn load_visible_asset_browser_thumbnails(&mut self) {
        // W63: the Unified Asset Browser is hosted exclusively by the right Assets
        // dock. Thumbnail loading follows that visible host instead of the retired
        // permanent left library panel.
        let rect = self.contextual_asset_browser_rect();
        if rect.w <= 0.0 || rect.h <= 0.0 {
            return;
        }
        let mut pending: Vec<(String, std::path::PathBuf)> = Vec::new();
        match self.viewport_mode {
            EditorViewportMode::PixelStudio => {
                if self.pixel_studio.library.is_empty() { return; }
                let grid = pixel_library_grid_rect(rect);
                let filtered = self.pixel_studio.filtered_library_indices();
                let start = self.pixel_studio.library_offset.min(filtered.len().saturating_sub(1));
                let capacity = browser_visible_capacity(grid);
                for &index in filtered.iter().skip(start).take(capacity) {
                    let Some(entry) = self.pixel_studio.library.get(index) else { continue; };
                    if self.unified_asset_browser.contains_or_failed(&entry.relative_path) { continue; }
                    pending.push((entry.relative_path.clone(), entry.path.clone()));
                    if pending.len() >= 2 { break; }
                }
            }
            EditorViewportMode::AnimationStudio => {
                if self.animation_studio.library.is_empty() { return; }
                let grid = super::animation_studio_render::animation_library_grid_rect(rect);
                let filtered = self.animation_studio.filtered_library_indices();
                let start = self.animation_studio.library_offset.min(filtered.len().saturating_sub(1));
                let capacity = browser_visible_capacity(grid);
                for &index in filtered.iter().skip(start).take(capacity) {
                    let Some(entry) = self.animation_studio.library.get(index) else { continue; };
                    if self.unified_asset_browser.contains_or_failed(&entry.relative_path) { continue; }
                    pending.push((entry.relative_path.clone(), entry.path.clone()));
                    if pending.len() >= 2 { break; }
                }
            }
            _ => return,
        }
        // Load at most one bounded thumbnail per frame. Full source sheets are
        // never uploaded merely for browser cards; the unified browser runtime
        // downsamples on CPU before creating a small nearest-filter GPU texture.
        if let Some((key, path)) = pending.into_iter().next() {
            if let Err(error) = self.unified_asset_browser.load_thumbnail(key, &path) {
                crate::append_editor_log(&format!("asset browser thumbnail skipped: {error}"));
            }
        }
        restore_editor_ui_render_state();
    }

    pub(crate) fn update_pixel_library_navigation(&mut self, rect: Rect, mouse: Vec2) -> bool {
        if !rect.contains(mouse) { return false; }
        let wheel = mouse_wheel().1;
        if wheel.abs() <= 0.05 { return false; }
        let filtered_count = self.pixel_studio.filtered_library_indices().len();
        let grid = pixel_library_grid_rect(rect);
        let columns = browser_columns(grid.w).max(1);
        let visible = browser_visible_capacity(grid).max(columns);
        let maximum = filtered_count.saturating_sub(visible);
        if wheel > 0.0 {
            self.pixel_studio.library_offset = self.pixel_studio.library_offset.saturating_sub(columns);
        } else {
            self.pixel_studio.library_offset = (self.pixel_studio.library_offset + columns).min(maximum);
        }
        true
    }

    pub(crate) fn handle_pixel_library_click(&mut self, mouse: Vec2, rect: Rect) -> bool {
        if pixel_refresh_rect(rect).contains(mouse) {
            self.unified_asset_browser.clear();
            self.status_message = match self.pixel_studio.refresh_library() {
                Ok(count) => format!("Rescanned Pixel Studio browser: {count} image assets"),
                Err(error) => error,
            };
            return true;
        }
        if pixel_library_search_rect(rect).contains(mouse) { self.text_focus = EditorTextFocus::PixelLibraryFilter; return true; }
        if pixel_library_clear_rect(rect).contains(mouse) {
            if !self.pixel_studio.library_filter.is_empty() {
                self.pixel_studio.library_filter.clear(); self.pixel_studio.library_offset = 0; self.status_message = "Pixel Asset search cleared".to_string();
            }
            return true;
        }
        if pixel_library_category_rect(rect).contains(mouse) {
            self.pixel_studio.cycle_library_category();
            let category = self
                .pixel_studio
                .active_library_category()
                .map(|value| value.label())
                .unwrap_or("All");
            self.status_message = format!("Pixel Asset category: {category}");
            return true;
        }
        let filtered = self.pixel_studio.filtered_library_indices();
        let grid = pixel_library_grid_rect(rect);
        let capacity = browser_visible_capacity(grid);
        let start = self.pixel_studio.library_offset.min(filtered.len().saturating_sub(1));
        for (slot, &index) in filtered.iter().skip(start).take(capacity).enumerate() {
            if browser_card_rect(grid, slot).contains(mouse) {
                self.pixel_studio.selected_entry = index;
                self.open_selected_pixel_library_entry();
                return true;
            }
        }
        true
    }

    pub(crate) fn open_selected_pixel_library_entry(&mut self) {
        let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| self.pixel_studio.load_selected()));
        self.status_message = match result {
            Ok(Ok(message)) => message,
            Ok(Err(error)) => format!("Pixel Studio could not open asset: {error}"),
            Err(payload) => {
                let detail = payload.downcast_ref::<&str>().copied().or_else(|| payload.downcast_ref::<String>().map(String::as_str)).unwrap_or("unknown asset-load panic");
                format!("Pixel Studio blocked an asset-load crash: {detail}. See logs/haven_editor_native_crash.log")
            }
        };
    }

    pub(crate) fn cycle_pixel_library(&mut self, delta: i32) {
        let indices = self.pixel_studio.filtered_library_indices();
        if indices.is_empty() { return; }
        let current = indices.iter().position(|index| *index == self.pixel_studio.selected_entry).unwrap_or(0);
        let next = cycle_index(current, indices.len(), delta);
        self.pixel_studio.selected_entry = indices[next];
        if next < self.pixel_studio.library_offset { self.pixel_studio.library_offset = next; }
    }
}
