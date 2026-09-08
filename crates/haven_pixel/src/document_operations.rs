use crate::layers::{composite_pixel, flatten_pair};
use crate::{PixelBlendMode, PixelClipboard, PixelDocument, PixelLayer, PixelLayerMetadata, PixelSelection};
use image::{imageops, Rgba, RgbaImage};

impl PixelDocument {
    /// Copies the active rectangular selection into an in-memory clipboard payload.
    /// `merged_visible` captures the document composite; otherwise only the active
    /// editable layer is copied. Clipboard provenance is retained for cross-document
    /// paste and Promote Selection.
    pub fn copy_selection_pixels(&self, merged_visible: bool) -> Option<PixelClipboard> {
        let selection = self.clamped_selection();
        if selection.is_empty() {
            return None;
        }
        let mut image = RgbaImage::from_pixel(
            selection.width,
            selection.height,
            Rgba([0, 0, 0, 0]),
        );
        for y in 0..selection.height {
            for x in 0..selection.width {
                let sx = selection.x + x;
                let sy = selection.y + y;
                let color = if merged_visible {
                    self.color_at(sx, sy)
                } else {
                    self.active_color_at(sx, sy)
                };
                image.put_pixel(x, y, Rgba(color));
            }
        }
        Some(PixelClipboard {
            image,
            source_asset_id: self.metadata.asset_id.clone(),
            source_display_name: self.metadata.display_name.clone(),
            source_layer_id: self.metadata.active_layer_id.clone(),
            source_selection: selection,
            pivot_offset: [
                self.metadata.pivot[0] - selection.x as i32,
                self.metadata.pivot[1] - selection.y as i32,
            ],
            source_license: self.metadata.license.clone(),
            merged_visible,
        })
    }

    /// Cuts the active-layer pixels in the current selection as one undoable edit.
    /// Merged-visible cut is intentionally unsupported because other visible layers
    /// are not implicitly destructive.
    pub fn cut_selection_pixels(&mut self) -> Option<PixelClipboard> {
        if !self.can_edit_active_layer() {
            return None;
        }
        let clipboard = self.copy_selection_pixels(false)?;
        let selection = self.clamped_selection();
        self.begin_edit();
        let clear = Rgba([0, 0, 0, 0]);
        for y in selection.y..selection.y.saturating_add(selection.height).min(self.height()) {
            for x in selection.x..selection.x.saturating_add(selection.width).min(self.width()) {
                self.active_layer_mut().image.put_pixel(x, y, clear);
            }
        }
        self.refresh_composite();
        self.dirty = true;
        Some(clipboard)
    }

    /// Pastes a clipboard payload onto the active layer and selects the pasted area.
    /// The operation is clipped to the document boundary and commits as one history
    /// transaction. Transparent clipboard pixels are intentional and replace the
    /// destination, matching rectangular pixel-selection semantics.
    pub fn paste_pixel_clipboard(&mut self, clipboard: &PixelClipboard, x: u32, y: u32) -> bool {
        if clipboard.is_empty() || !self.can_edit_active_layer() || self.width() == 0 || self.height() == 0 {
            return false;
        }
        let x = x.min(self.width().saturating_sub(1));
        let y = y.min(self.height().saturating_sub(1));
        let width = clipboard.width().min(self.width().saturating_sub(x));
        let height = clipboard.height().min(self.height().saturating_sub(y));
        if width == 0 || height == 0 {
            return false;
        }
        self.begin_edit();
        for dy in 0..height {
            for dx in 0..width {
                let pixel = *clipboard.image.get_pixel(dx, dy);
                self.active_layer_mut().image.put_pixel(x + dx, y + dy, pixel);
            }
        }
        self.metadata.selection = PixelSelection { x, y, width, height };
        self.refresh_composite();
        self.dirty = true;
        true
    }

    /// Duplicates the active selection by one pixel down/right where possible.
    /// The returned clipboard is suitable for keeping the editor clipboard in sync.
    pub fn duplicate_selection_pixels(&mut self) -> Option<PixelClipboard> {
        let clipboard = self.copy_selection_pixels(false)?;
        let selection = self.clamped_selection();
        let max_x = self.width().saturating_sub(clipboard.width());
        let max_y = self.height().saturating_sub(clipboard.height());
        let x = selection.x.saturating_add(1).min(max_x);
        let y = selection.y.saturating_add(1).min(max_y);
        if self.paste_pixel_clipboard(&clipboard, x, y) {
            Some(clipboard)
        } else {
            None
        }
    }

    pub fn flip_selection_horizontal(&mut self) {
        self.flip_selection(true);
    }

    pub fn flip_selection_vertical(&mut self) {
        self.flip_selection(false);
    }


    pub fn rotate_selection_clockwise(&mut self) -> bool {
        let selection = self.clamped_selection();
        if selection.is_empty() || !self.can_edit_active_layer() { return false; }
        self.begin_edit();
        let crop = imageops::crop_imm(&self.active_layer().image, selection.x, selection.y, selection.width, selection.height).to_image();
        let rotated = imageops::rotate90(&crop);
        let pivot_before = self.metadata.pivot;
        let pivot_inside = point_in_selection(pivot_before, selection);
        let mirrored_pivot = if pivot_inside {
            let local_x = pivot_before[0] - selection.x as i32;
            let local_y = pivot_before[1] - selection.y as i32;
            Some([
                selection.x as i32 + selection.height.saturating_sub(1) as i32 - local_y,
                selection.y as i32 + local_x,
            ])
        } else {
            None
        };
        let clear = Rgba([0, 0, 0, 0]);
        for y in selection.y..selection.y.saturating_add(selection.height).min(self.height()) {
            for x in selection.x..selection.x.saturating_add(selection.width).min(self.width()) {
                self.active_layer_mut().image.put_pixel(x, y, clear);
            }
        }
        imageops::replace(&mut self.active_layer_mut().image, &rotated, selection.x as i64, selection.y as i64);
        self.metadata.selection.width = rotated.width().min(self.width().saturating_sub(selection.x));
        self.metadata.selection.height = rotated.height().min(self.height().saturating_sub(selection.y));
        if let Some(pivot) = mirrored_pivot {
            self.metadata.pivot = clamp_point_to_document(pivot, self.width(), self.height());
        }
        self.refresh_composite(); self.dirty = true; true
    }

    /// W61C: nearest-neighbor selection resize used by the shared Transform Gizmo.
    /// The operation remains pixel-safe and commits as a single document history step.
    pub fn resize_selection_nearest(&mut self, new_width: u32, new_height: u32) -> bool {
        let selection = self.clamped_selection();
        if selection.is_empty() || !self.can_edit_active_layer() {
            return false;
        }
        let max_width = self.width().saturating_sub(selection.x).max(1);
        let max_height = self.height().saturating_sub(selection.y).max(1);
        let new_width = new_width.clamp(1, max_width);
        let new_height = new_height.clamp(1, max_height);
        if new_width == selection.width && new_height == selection.height {
            return false;
        }
        let mapped_pivot = map_pivot_between_selections(
            self.metadata.pivot,
            selection,
            PixelSelection { x: selection.x, y: selection.y, width: new_width, height: new_height },
        );
        self.begin_edit();
        let crop = imageops::crop_imm(
            &self.active_layer().image,
            selection.x,
            selection.y,
            selection.width,
            selection.height,
        )
        .to_image();
        let resized = imageops::resize(
            &crop,
            new_width,
            new_height,
            imageops::FilterType::Nearest,
        );
        let clear = Rgba([0, 0, 0, 0]);
        let clear_width = selection.width.max(new_width);
        let clear_height = selection.height.max(new_height);
        for y in selection.y..selection.y.saturating_add(clear_height).min(self.height()) {
            for x in selection.x..selection.x.saturating_add(clear_width).min(self.width()) {
                self.active_layer_mut().image.put_pixel(x, y, clear);
            }
        }
        imageops::replace(
            &mut self.active_layer_mut().image,
            &resized,
            selection.x as i64,
            selection.y as i64,
        );
        self.metadata.selection.width = new_width;
        self.metadata.selection.height = new_height;
        if let Some(pivot) = mapped_pivot {
            self.metadata.pivot = clamp_point_to_document(pivot, self.width(), self.height());
        }
        self.refresh_composite();
        self.dirty = true;
        true
    }

    /// W61C: move/stretch/scale the active pixel selection into an explicit
    /// destination rectangle using nearest-neighbor sampling. This is the commit
    /// primitive for the shared eight-handle Transform Gizmo.
    pub fn transform_selection_nearest(&mut self, destination: PixelSelection) -> bool {
        let selection = self.clamped_selection();
        if selection.is_empty() || !self.can_edit_active_layer() {
            return false;
        }
        let mut destination = destination;
        destination.x = destination.x.min(self.width().saturating_sub(1));
        destination.y = destination.y.min(self.height().saturating_sub(1));
        destination.width = destination
            .width
            .max(1)
            .min(self.width().saturating_sub(destination.x));
        destination.height = destination
            .height
            .max(1)
            .min(self.height().saturating_sub(destination.y));
        if destination == selection {
            return false;
        }
        let crop = imageops::crop_imm(
            &self.active_layer().image,
            selection.x,
            selection.y,
            selection.width,
            selection.height,
        )
        .to_image();
        let transformed = imageops::resize(
            &crop,
            destination.width,
            destination.height,
            imageops::FilterType::Nearest,
        );
        let mapped_pivot = map_pivot_between_selections(self.metadata.pivot, selection, destination);
        self.begin_edit();
        let clear = Rgba([0, 0, 0, 0]);
        for region in [selection, destination] {
            for y in region.y..region.y.saturating_add(region.height).min(self.height()) {
                for x in region.x..region.x.saturating_add(region.width).min(self.width()) {
                    self.active_layer_mut().image.put_pixel(x, y, clear);
                }
            }
        }
        imageops::replace(
            &mut self.active_layer_mut().image,
            &transformed,
            destination.x as i64,
            destination.y as i64,
        );
        self.metadata.selection = destination;
        if let Some(pivot) = mapped_pivot {
            self.metadata.pivot = clamp_point_to_document(pivot, self.width(), self.height());
        }
        self.refresh_composite();
        self.dirty = true;
        true
    }

    /// W61C: arbitrary nearest-neighbor rotation around an explicit document-space pivot.
    /// The rotated selection is re-bounded while keeping the requested pivot registered
    /// to the same world/document coordinate as closely as integer pixels permit.
    pub fn rotate_selection_degrees(
        &mut self,
        angle_degrees: f32,
        pivot_document: [f32; 2],
    ) -> bool {
        let selection = self.clamped_selection();
        if selection.is_empty() || !self.can_edit_active_layer() || angle_degrees.abs() < 0.001 {
            return false;
        }
        let crop = imageops::crop_imm(
            &self.active_layer().image,
            selection.x,
            selection.y,
            selection.width,
            selection.height,
        )
        .to_image();
        let pivot_local = [
            pivot_document[0] - selection.x as f32,
            pivot_document[1] - selection.y as f32,
        ];
        let radians = angle_degrees.to_radians();
        let sin = radians.sin();
        let cos = radians.cos();
        let rotate = |x: f32, y: f32| -> [f32; 2] {
            let dx = x - pivot_local[0];
            let dy = y - pivot_local[1];
            [
                pivot_local[0] + dx * cos - dy * sin,
                pivot_local[1] + dx * sin + dy * cos,
            ]
        };
        let corners = [
            rotate(0.0, 0.0),
            rotate(selection.width as f32, 0.0),
            rotate(0.0, selection.height as f32),
            rotate(selection.width as f32, selection.height as f32),
        ];
        let min_x = corners.iter().map(|p| p[0]).fold(f32::INFINITY, f32::min).floor();
        let min_y = corners.iter().map(|p| p[1]).fold(f32::INFINITY, f32::min).floor();
        let max_x = corners.iter().map(|p| p[0]).fold(f32::NEG_INFINITY, f32::max).ceil();
        let max_y = corners.iter().map(|p| p[1]).fold(f32::NEG_INFINITY, f32::max).ceil();
        let out_width = ((max_x - min_x).max(1.0)) as u32;
        let out_height = ((max_y - min_y).max(1.0)) as u32;
        let mut rotated = RgbaImage::from_pixel(out_width, out_height, Rgba([0, 0, 0, 0]));
        let inv_sin = (-radians).sin();
        let inv_cos = (-radians).cos();
        for dy in 0..out_height {
            for dx in 0..out_width {
                let rx = min_x + dx as f32 + 0.5;
                let ry = min_y + dy as f32 + 0.5;
                let ox = rx - pivot_local[0];
                let oy = ry - pivot_local[1];
                let sx = pivot_local[0] + ox * inv_cos - oy * inv_sin;
                let sy = pivot_local[1] + ox * inv_sin + oy * inv_cos;
                if sx >= 0.0
                    && sy >= 0.0
                    && sx < selection.width as f32
                    && sy < selection.height as f32
                {
                    let source_x = sx.floor() as u32;
                    let source_y = sy.floor() as u32;
                    rotated.put_pixel(dx, dy, *crop.get_pixel(source_x, source_y));
                }
            }
        }

        let desired_x = selection.x as i32 + min_x as i32;
        let desired_y = selection.y as i32 + min_y as i32;
        let new_x = desired_x.clamp(0, self.width().saturating_sub(1) as i32) as u32;
        let new_y = desired_y.clamp(0, self.height().saturating_sub(1) as i32) as u32;
        let clipped_width = out_width.min(self.width().saturating_sub(new_x)).max(1);
        let clipped_height = out_height.min(self.height().saturating_sub(new_y)).max(1);

        self.begin_edit();
        let clear = Rgba([0, 0, 0, 0]);
        for y in selection.y..selection.y.saturating_add(selection.height).min(self.height()) {
            for x in selection.x..selection.x.saturating_add(selection.width).min(self.width()) {
                self.active_layer_mut().image.put_pixel(x, y, clear);
            }
        }
        let clipped = imageops::crop_imm(&rotated, 0, 0, clipped_width, clipped_height).to_image();
        imageops::replace(
            &mut self.active_layer_mut().image,
            &clipped,
            new_x as i64,
            new_y as i64,
        );
        self.metadata.selection = PixelSelection {
            x: new_x,
            y: new_y,
            width: clipped_width,
            height: clipped_height,
        };
        self.refresh_composite();
        self.dirty = true;
        true
    }

    pub fn nudge_selection(&mut self, dx: i32, dy: i32) -> bool {
        let selection = self.clamped_selection();
        if selection.is_empty() || !self.can_edit_active_layer() { return false; }
        let nx = (selection.x as i32 + dx).clamp(0, self.width().saturating_sub(selection.width) as i32) as u32;
        let ny = (selection.y as i32 + dy).clamp(0, self.height().saturating_sub(selection.height) as i32) as u32;
        if nx == selection.x && ny == selection.y { return false; }
        let mapped_pivot = map_pivot_between_selections(
            self.metadata.pivot,
            selection,
            PixelSelection { x: nx, y: ny, width: selection.width, height: selection.height },
        );
        self.begin_edit();
        let crop = imageops::crop_imm(&self.active_layer().image, selection.x, selection.y, selection.width, selection.height).to_image();
        for y in selection.y..selection.y + selection.height { for x in selection.x..selection.x + selection.width { self.active_layer_mut().image.put_pixel(x,y,Rgba([0,0,0,0])); } }
        imageops::replace(&mut self.active_layer_mut().image, &crop, nx as i64, ny as i64);
        self.metadata.selection.x = nx; self.metadata.selection.y = ny;
        if let Some(pivot) = mapped_pivot {
            self.metadata.pivot = clamp_point_to_document(pivot, self.width(), self.height());
        }
        self.refresh_composite(); self.dirty = true; true
    }

    pub fn select_opaque_bounds(&mut self) -> bool {
        let image = &self.active_layer().image;
        let (mut min_x, mut min_y, mut max_x, mut max_y) = (self.width(), self.height(), 0, 0);
        let mut found = false;
        for (x,y,p) in image.enumerate_pixels() { if p[3] != 0 { found=true; min_x=min_x.min(x); min_y=min_y.min(y); max_x=max_x.max(x); max_y=max_y.max(y); } }
        if !found { return false; }
        self.metadata.selection = PixelSelection { x:min_x, y:min_y, width:max_x-min_x+1, height:max_y-min_y+1 }; true
    }

    pub fn select_color_bounds(&mut self, color: [u8;4]) -> bool {
        let image = &self.active_layer().image;
        let (mut min_x, mut min_y, mut max_x, mut max_y) = (self.width(), self.height(), 0, 0);
        let mut found=false;
        for (x,y,p) in image.enumerate_pixels() { if p.0 == color { found=true; min_x=min_x.min(x); min_y=min_y.min(y); max_x=max_x.max(x); max_y=max_y.max(y); } }
        if !found { return false; }
        self.metadata.selection = PixelSelection { x:min_x, y:min_y, width:max_x-min_x+1, height:max_y-min_y+1 }; true
    }

    pub fn add_layer(&mut self, name: impl Into<String>) -> usize {
        self.begin_edit();
        let id = self.next_layer_id();
        let width = self.width();
        let height = self.height();
        self.layers.push(PixelLayer {
            metadata: PixelLayerMetadata::new(&id, name),
            image: RgbaImage::from_pixel(width, height, Rgba([0, 0, 0, 0])),
        });
        self.metadata.active_layer_id = id;
        self.sync_layer_metadata();
        self.dirty = true;
        self.layers.len() - 1
    }

    pub fn duplicate_active_layer(&mut self) -> usize {
        self.begin_edit();
        let source = self.active_layer().clone();
        let id = self.next_layer_id();
        let mut metadata = source.metadata;
        metadata.id = id.clone();
        metadata.name = format!("{} Copy", metadata.name);
        metadata.image_path.clear();
        let index = self.active_layer_index() + 1;
        self.layers.insert(
            index,
            PixelLayer {
                metadata,
                image: source.image,
            },
        );
        self.metadata.active_layer_id = id;
        self.sync_layer_metadata();
        self.refresh_composite();
        self.dirty = true;
        index
    }

    pub fn delete_active_layer(&mut self) -> bool {
        if self.layers.len() <= 1 {
            return false;
        }
        self.begin_edit();
        let index = self.active_layer_index();
        self.layers.remove(index);
        let next = index.saturating_sub(1).min(self.layers.len() - 1);
        self.metadata.active_layer_id = self.layers[next].metadata.id.clone();
        self.sync_layer_metadata();
        self.refresh_composite();
        self.dirty = true;
        true
    }

    pub fn move_active_layer(&mut self, delta: i32) -> bool {
        let index = self.active_layer_index();
        let target =
            (index as i32 + delta).clamp(0, self.layers.len().saturating_sub(1) as i32) as usize;
        self.move_active_layer_to(target)
    }

    /// Move the active layer to an exact stack index while preserving the
    /// relative order of every intervening layer. This is the authority used by
    /// the native editor's drag-to-reorder Layer Rail.
    pub fn move_active_layer_to(&mut self, target: usize) -> bool {
        let index = self.active_layer_index();
        let target = target.min(self.layers.len().saturating_sub(1));
        if target == index {
            return false;
        }
        self.begin_edit();
        let layer = self.layers.remove(index);
        self.layers.insert(target, layer);
        self.metadata.active_layer_id = self.layers[target].metadata.id.clone();
        self.sync_layer_metadata();
        self.refresh_composite();
        self.dirty = true;
        true
    }

    pub fn merge_active_down(&mut self) -> bool {
        let index = self.active_layer_index();
        if index == 0 {
            return false;
        }
        self.begin_edit();
        let top = self.layers.remove(index);
        let bottom = self.layers.remove(index - 1);
        let image = flatten_pair(&bottom, &top);
        let mut metadata = bottom.metadata;
        metadata.name = format!("{} + {}", metadata.name, top.metadata.name);
        metadata.opacity = u8::MAX;
        metadata.blend_mode = PixelBlendMode::Normal;
        metadata.visible = true;
        metadata.locked = false;
        metadata.image_path.clear();
        let id = metadata.id.clone();
        self.layers
            .insert(index - 1, PixelLayer { metadata, image });
        self.metadata.active_layer_id = id;
        self.sync_layer_metadata();
        self.refresh_composite();
        self.dirty = true;
        true
    }

    pub fn rename_active_layer(&mut self, name: impl Into<String>) -> bool {
        let name = name.into().trim().to_string();
        if name.is_empty() || self.active_layer().metadata.name == name {
            return false;
        }
        self.begin_edit();
        self.active_layer_mut().metadata.name = name;
        self.sync_layer_metadata();
        self.dirty = true;
        true
    }

    pub fn toggle_active_layer_visibility(&mut self) {
        self.begin_edit();
        let layer = self.active_layer_mut();
        layer.metadata.visible = !layer.metadata.visible;
        self.sync_layer_metadata();
        self.refresh_composite();
        self.dirty = true;
    }

    pub fn toggle_active_layer_lock(&mut self) {
        self.begin_edit();
        let layer = self.active_layer_mut();
        layer.metadata.locked = !layer.metadata.locked;
        self.sync_layer_metadata();
        self.dirty = true;
    }

    pub fn adjust_active_layer_opacity(&mut self, delta: i16) {
        let opacity = (self.active_layer().metadata.opacity as i16 + delta).clamp(0, 255) as u8;
        let _ = self.set_active_layer_opacity(opacity);
    }

    pub fn set_active_layer_opacity(&mut self, opacity: u8) -> bool {
        if self.active_layer().metadata.opacity == opacity {
            return false;
        }
        self.begin_edit();
        self.active_layer_mut().metadata.opacity = opacity;
        self.sync_layer_metadata();
        self.refresh_composite();
        self.dirty = true;
        true
    }

    pub fn set_active_layer_blend_mode(&mut self, mode: PixelBlendMode) -> bool {
        if self.active_layer().metadata.blend_mode == mode {
            return false;
        }
        self.begin_edit();
        self.active_layer_mut().metadata.blend_mode = mode;
        self.sync_layer_metadata();
        self.refresh_composite();
        self.dirty = true;
        true
    }

    pub fn cycle_active_layer_blend_mode(&mut self) {
        self.begin_edit();
        let layer = self.active_layer_mut();
        layer.metadata.blend_mode = layer.metadata.blend_mode.next();
        self.sync_layer_metadata();
        self.refresh_composite();
        self.dirty = true;
    }

    pub fn resize_canvas(&mut self, width: u32, height: u32) -> bool {
        let width = width.clamp(1, 8192);
        let height = height.clamp(1, 8192);
        if width == self.width() && height == self.height() {
            return false;
        }
        self.begin_edit();
        for layer in &mut self.layers {
            let mut resized = RgbaImage::from_pixel(width, height, Rgba([0, 0, 0, 0]));
            imageops::replace(&mut resized, &layer.image, 0, 0);
            layer.image = resized;
        }
        self.metadata.width = width;
        self.metadata.height = height;
        self.clamp_document_metadata();
        self.refresh_composite();
        self.dirty = true;
        true
    }

    pub fn crop_to_selection(&mut self) -> bool {
        let selection = self.clamped_selection();
        if selection.is_empty()
            || (selection.x == 0
                && selection.y == 0
                && selection.width == self.width()
                && selection.height == self.height())
        {
            return false;
        }
        self.begin_edit();
        self.apply_crop(selection);
        true
    }

    pub fn trim_transparent_padding(&mut self) -> bool {
        let mut min_x = self.width();
        let mut min_y = self.height();
        let mut max_x = 0;
        let mut max_y = 0;
        let mut found = false;
        for (x, y, pixel) in self.composite.enumerate_pixels() {
            if pixel[3] == 0 {
                continue;
            }
            found = true;
            min_x = min_x.min(x);
            min_y = min_y.min(y);
            max_x = max_x.max(x);
            max_y = max_y.max(y);
        }
        if !found {
            return false;
        }
        let selection = PixelSelection {
            x: min_x,
            y: min_y,
            width: max_x - min_x + 1,
            height: max_y - min_y + 1,
        };
        if selection.x == 0
            && selection.y == 0
            && selection.width == self.width()
            && selection.height == self.height()
        {
            return false;
        }
        self.begin_edit();
        self.apply_crop(selection);
        true
    }

    fn apply_crop(&mut self, selection: PixelSelection) {
        for layer in &mut self.layers {
            layer.image = imageops::crop_imm(
                &layer.image,
                selection.x,
                selection.y,
                selection.width,
                selection.height,
            )
            .to_image();
        }
        self.metadata.width = selection.width;
        self.metadata.height = selection.height;
        self.metadata.selection = PixelSelection {
            x: 0,
            y: 0,
            width: selection.width,
            height: selection.height,
        };
        self.metadata.pivot[0] -= selection.x as i32;
        self.metadata.pivot[1] -= selection.y as i32;
        self.metadata.grid.offset_x -= selection.x as i32;
        self.metadata.grid.offset_y -= selection.y as i32;
        self.clamp_document_metadata();
        self.refresh_composite();
        self.dirty = true;
    }

    fn flip_selection(&mut self, horizontal: bool) {
        let selection = self.clamped_selection();
        if selection.is_empty() || !self.can_edit_active_layer() {
            return;
        }
        let pivot_before = self.metadata.pivot;
        let mirrored_pivot = if point_in_selection(pivot_before, selection) {
            let local_x = pivot_before[0] - selection.x as i32;
            let local_y = pivot_before[1] - selection.y as i32;
            Some(if horizontal {
                [
                    selection.x as i32 + selection.width.saturating_sub(1) as i32 - local_x,
                    pivot_before[1],
                ]
            } else {
                [
                    pivot_before[0],
                    selection.y as i32 + selection.height.saturating_sub(1) as i32 - local_y,
                ]
            })
        } else {
            None
        };
        self.begin_edit();
        let crop = imageops::crop_imm(
            &self.active_layer().image,
            selection.x,
            selection.y,
            selection.width,
            selection.height,
        )
        .to_image();
        let flipped = if horizontal {
            imageops::flip_horizontal(&crop)
        } else {
            imageops::flip_vertical(&crop)
        };
        imageops::replace(
            &mut self.active_layer_mut().image,
            &flipped,
            selection.x as i64,
            selection.y as i64,
        );
        if let Some(pivot) = mirrored_pivot {
            self.metadata.pivot = clamp_point_to_document(pivot, self.width(), self.height());
        }
        self.refresh_composite();
        self.dirty = true;
    }

    pub(crate) fn refresh_composite_pixel(&mut self, x: u32, y: u32) {
        let pixel = composite_pixel(&self.layers, x, y);
        self.composite.put_pixel(x, y, Rgba(pixel));
    }

    fn clamped_selection(&self) -> PixelSelection {
        let mut selection = self.metadata.selection;
        selection.x = selection.x.min(self.width().saturating_sub(1));
        selection.y = selection.y.min(self.height().saturating_sub(1));
        selection.width = selection
            .width
            .min(self.width().saturating_sub(selection.x));
        selection.height = selection
            .height
            .min(self.height().saturating_sub(selection.y));
        selection
    }

    fn clamp_document_metadata(&mut self) {
        let width = self.width().max(1) as i32;
        let height = self.height().max(1) as i32;
        self.metadata.selection = self.clamped_selection();
        self.metadata.pivot[0] = self.metadata.pivot[0].clamp(0, width - 1);
        self.metadata.pivot[1] = self.metadata.pivot[1].clamp(0, height - 1);
    }

    fn next_layer_id(&self) -> String {
        let mut number = self.layers.len() + 1;
        loop {
            let id = format!("layer_{number:03}");
            if !self.layers.iter().any(|layer| layer.metadata.id == id) {
                return id;
            }
            number += 1;
        }
    }
}

fn point_in_selection(point: [i32; 2], selection: PixelSelection) -> bool {
    point[0] >= selection.x as i32
        && point[1] >= selection.y as i32
        && point[0] < selection.x.saturating_add(selection.width) as i32
        && point[1] < selection.y.saturating_add(selection.height) as i32
}

fn map_pivot_between_selections(
    pivot: [i32; 2],
    source: PixelSelection,
    destination: PixelSelection,
) -> Option<[i32; 2]> {
    if !point_in_selection(pivot, source) || source.width == 0 || source.height == 0 {
        return None;
    }
    let local_x = pivot[0] - source.x as i32;
    let local_y = pivot[1] - source.y as i32;
    let mapped_x = if source.width <= 1 || destination.width <= 1 {
        0
    } else {
        ((local_x as f32 / source.width.saturating_sub(1) as f32)
            * destination.width.saturating_sub(1) as f32)
            .round() as i32
    };
    let mapped_y = if source.height <= 1 || destination.height <= 1 {
        0
    } else {
        ((local_y as f32 / source.height.saturating_sub(1) as f32)
            * destination.height.saturating_sub(1) as f32)
            .round() as i32
    };
    Some([
        destination.x as i32 + mapped_x,
        destination.y as i32 + mapped_y,
    ])
}

fn clamp_point_to_document(point: [i32; 2], width: u32, height: u32) -> [i32; 2] {
    [
        point[0].clamp(0, width.saturating_sub(1) as i32),
        point[1].clamp(0, height.saturating_sub(1) as i32),
    ]
}

