//! Runtime Resource Context integration for Animation Studio.
//!
//! Kept separate from the core studio state so runtime-selection plumbing does
//! not grow the animation authoring surface or become a second document model.

use super::*;
use haven_pixel::{
    AnimationClip, AnimationDirection, AnimationDocument, AnimationFrame, AnimationLoopMode,
    PixelSelection,
};

impl AnimationStudioState {
    pub(crate) fn load_direct_source(
        &mut self,
        source_path: &std::path::Path,
        display_name: &str,
    ) -> Result<String, String> {
        let image = image::open(source_path)
            .map_err(|error| format!("failed to load {}: {error}", source_path.display()))?
            .to_rgba8();
        if image.width() > u16::MAX as u32 || image.height() > u16::MAX as u32 {
            return Err("source image exceeds Macroquad texture limits".to_string());
        }
        let texture =
            Texture2D::from_rgba8(image.width() as u16, image.height() as u16, image.as_raw());
        texture.set_filter(FilterMode::Nearest);
        let document = AnimationDocument::load_or_create(
            source_path,
            display_name,
            haven_pixel::PixelLicense::default(),
            image.width(),
            image.height(),
        )?;
        self.document = Some(document);
        self.texture = Some(texture);
        self.source_cell = [0, 0];
        self.playing = false;
        self.playback_elapsed_ms = 0.0;
        Ok(format!("Opened {display_name} from runtime Resource Context"))
    }

    /// Seed an otherwise metadata-empty resolved ULPC sheet with contextual
    /// clips, then select the exact source frame published by runtime. Existing
    /// authored animation metadata always wins and is never replaced.
    pub(crate) fn apply_runtime_source_context(
        &mut self,
        action_id: &str,
        direction: &str,
        source_frame_index: usize,
        frame_size: u32,
    ) -> Vec<String> {
        let needs_context_clip = self
            .document
            .as_ref()
            .is_some_and(|document| document.metadata.clips.iter().all(|clip| clip.frames.is_empty()));
        if needs_context_clip {
            if let Some(document) = self.document.as_mut() {
                let clips = runtime_context_clips(
                    action_id,
                    frame_size.max(1),
                    document.metadata.image_width,
                    document.metadata.image_height,
                );
                if !clips.is_empty() {
                    document.metadata.frame_width = frame_size.max(1);
                    document.metadata.frame_height = frame_size.max(1);
                    document.metadata.grid_offset = [0, 0];
                    document.metadata.clips = clips;
                    document.selected_clip = 0;
                    document.selected_frame = 0;
                    // Contextual clip synthesis describes the source that already
                    // exists; it is not itself an authored mutation.
                    document.dirty = false;
                }
            }
        }
        self.apply_runtime_frame_context(direction, source_frame_index)
    }

    pub(crate) fn apply_runtime_frame_context(
        &mut self,
        direction: &str,
        source_frame_index: usize,
    ) -> Vec<String> {
        let (source_cell, sockets) = {
            let Some(document) = self.document.as_mut() else {
                return Vec::new();
            };
            let direction_key = direction.to_ascii_lowercase();
            let direction_match = |clip_direction: haven_pixel::AnimationDirection| -> bool {
                matches!(
                    (direction_key.as_str(), clip_direction),
                    ("south", haven_pixel::AnimationDirection::South)
                        | ("west", haven_pixel::AnimationDirection::West)
                        | ("north", haven_pixel::AnimationDirection::North)
                        | ("east", haven_pixel::AnimationDirection::East)
                )
            };
            if let Some(index) = document
                .metadata
                .clips
                .iter()
                .position(|clip| direction_match(clip.direction))
            {
                document.selected_clip = index;
            }
            let frame_width = document.metadata.frame_width.max(1);
            let frame_height = document.metadata.frame_height.max(1);
            let grid_offset_x = document.metadata.grid_offset[0].max(0) as u32;
            let grid_offset_y = document.metadata.grid_offset[1].max(0) as u32;
            let selected = document.clip().and_then(|clip| {
                clip.frames.iter().position(|frame| {
                    frame.source.x.saturating_sub(grid_offset_x) / frame_width
                        == source_frame_index as u32
                })
            });
            let frame_count = document.clip().map_or(0, |clip| clip.frames.len());
            if frame_count > 0 {
                document.selected_frame = selected
                    .unwrap_or_else(|| source_frame_index.min(frame_count.saturating_sub(1)));
            }
            let source_cell = document.frame().map(|frame| {
                [
                    frame.source.x.saturating_sub(grid_offset_x) / frame_width,
                    frame.source.y.saturating_sub(grid_offset_y) / frame_height,
                ]
            });
            let sockets = document
                .frame()
                .map(|frame| {
                    frame
                        .sockets
                        .iter()
                        .map(|socket| socket.kind.code().to_string())
                        .collect()
                })
                .unwrap_or_default();
            (source_cell, sockets)
        };
        if let Some(source_cell) = source_cell {
            self.source_cell = source_cell;
        }
        sockets
    }


}

fn runtime_context_direction(value: &str) -> Option<(AnimationDirection, u32)> {
    Some(match value {
        "north" => (AnimationDirection::North, 0),
        "west" => (AnimationDirection::West, 1),
        "south" => (AnimationDirection::South, 2),
        "east" => (AnimationDirection::East, 3),
        _ => return None,
    })
}

fn runtime_context_clips(
    action_id: &str,
    frame_size: u32,
    image_width: u32,
    image_height: u32,
) -> Vec<AnimationClip> {
    let frame_size = frame_size.max(1);
    let columns = image_width / frame_size;
    let rows = image_height / frame_size;
    if columns == 0 || rows == 0 {
        return Vec::new();
    }
    let requested_frames = haven_assets::universal_lpc_animation::animation_spec(action_id)
        .map(|spec| spec.cycle.to_vec())
        .unwrap_or_else(|| (0..columns as usize).collect());
    let directions: &[&str] = if rows >= 4 {
        &["north", "west", "south", "east"]
    } else {
        &["south"]
    };
    let mut clips = Vec::new();
    for (clip_index, direction_name) in directions.iter().enumerate() {
        let Some((direction, canonical_row)) = runtime_context_direction(direction_name) else {
            continue;
        };
        let row = if rows >= 4 { canonical_row.min(rows - 1) } else { 0 };
        let mut clip = AnimationClip::new(clip_index + 1);
        clip.id = format!("runtime_{action_id}_{direction_name}");
        clip.display_name = format!("{} {}", action_id.replace('_', " "), direction_name);
        clip.direction = direction;
        clip.loop_mode = AnimationLoopMode::Loop;
        let default_frame_duration_ms = clip.default_frame_duration_ms;
        clip.frames = requested_frames
            .iter()
            .copied()
            .filter(|frame| (*frame as u32) < columns)
            .map(|frame| {
                AnimationFrame::new(
                    PixelSelection {
                        x: frame as u32 * frame_size,
                        y: row * frame_size,
                        width: frame_size,
                        height: frame_size,
                    },
                    default_frame_duration_ms,
                )
            })
            .collect();
        if !clip.frames.is_empty() {
            clips.push(clip);
        }
    }
    clips
}

