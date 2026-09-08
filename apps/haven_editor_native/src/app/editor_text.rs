use macroquad::prelude::*;
use std::cell::RefCell;
use std::path::{Path, PathBuf};
use std::sync::OnceLock;

const DEFAULT_EDITOR_TEXT_SCALE: f32 = 1.10;
/// Fixed logical raster tiers for the persistent editor font atlas.
///
/// Macroquad caches glyphs by `(character, raster_size)` and grows/recreates the
/// atlas texture when a new size no longer fits. Havenwild therefore keeps the
/// number of raster sizes bounded and uses `font_scale` for the final on-screen
/// size. This prevents ordinary UI actions from causing a font-atlas resize in
/// the middle of an already batched frame.
const EDITOR_FONT_RASTER_TIERS: [u16; 5] = [14, 18, 24, 32, 40];
static EDITOR_TEXT_SCALE: OnceLock<f32> = OnceLock::new();

thread_local! {
    /// Dedicated Segoe UI editor font atlas.
    ///
    /// W60B keeps the Windows UI face as the normal editor authority. The atlas
    /// is created only after Macroquad has completed one stable frame, then
    /// pre-warmed before any visible loading text is drawn. This avoids both the
    /// old fallback-font flash and the early-frame black-glyph failure without
    /// abandoning the intended Segoe UI typography.
    static EDITOR_UI_FONT: RefCell<Option<Font>> = const { RefCell::new(None) };
}

pub(crate) fn editor_text_scale() -> f32 {
    *EDITOR_TEXT_SCALE.get_or_init(|| {
        std::env::var("HAVENWILD_EDITOR_TEXT_SCALE")
            .ok()
            .and_then(|value| value.trim().parse::<f32>().ok())
            .filter(|value| value.is_finite())
            .or_else(|| {
                std::fs::read_to_string(super::editor_settings::NATIVE_EDITOR_SETTINGS_PATH)
                    .ok()
                    .and_then(|text| serde_json::from_str::<serde_json::Value>(&text).ok())
                    .and_then(|value| value.get("ui_text_scale").and_then(|value| value.as_f64()))
                    .map(|value| value as f32)
            })
            .map(|value| value.clamp(0.90, 1.35))
            .unwrap_or(DEFAULT_EDITOR_TEXT_SCALE)
    })
}

pub(crate) fn initialize_editor_font() -> String {
    if editor_font_ready() {
        return "Editor UI font atlas already initialized".to_string();
    }
    let candidates = editor_font_candidates();
    for path in candidates {
        let Ok(bytes) = std::fs::read(&path) else {
            continue;
        };
        match load_ttf_font_from_bytes(&bytes) {
            Ok(mut font) => {
                // Keep Segoe independent from the pixel-art texture policy.
                // Macroquad otherwise inherits the current default texture
                // filter when the font is created.
                font.set_filter(FilterMode::Linear);
                EDITOR_UI_FONT.with(|slot| *slot.borrow_mut() = Some(font));
                return format!("Editor UI font atlas loaded from {}", path.display());
            }
            Err(_) => continue,
        }
    }

    EDITOR_UI_FONT.with(|slot| *slot.borrow_mut() = None);
    "Editor UI font atlas unavailable; Macroquad fallback font active".to_string()
}

pub(crate) fn prewarm_editor_font() {
    set_default_camera();
    gl_use_default_material();
    let dpi = macroquad::miniquad::window::dpi_scale().max(1.0);
    EDITOR_UI_FONT.with(|slot| {
        let font = slot.borrow();
        if let Some(font) = font.as_ref() {
            // Macroquad's Font atlas is dynamic: each previously unseen
            // (glyph, raster-size) pair is inserted into one atlas and the GPU
            // texture is recreated when the atlas grows. If that happens after
            // text has already been queued in the current frame, older text can
            // reference the texture that Macroquad just replaced.
            //
            // Populate every Havenwild raster tier before the first visible UI
            // frame. `populate_font_cache` changes the atlas without emitting
            // draw batches, so any required growth happens while no visible
            // text references the old GPU texture. Latin-1 covers the normal
            // editor chrome plus common Windows/project filenames.
            let glyphs = Font::ascii_character_list();
            for logical_size in EDITOR_FONT_RASTER_TIERS {
                let raster_size = (logical_size as f32 * dpi).ceil() as u16;
                font.populate_font_cache(&glyphs, raster_size.max(1));
            }

            // Force the fully populated atlas to upload/recreate now, while the
            // warm-up frame is still intentionally invisible. Subsequent UI
            // draws reuse the same atlas and the bounded raster tiers below.
            let _ = draw_text_ex(
                "Havenwild editor font atlas warmup",
                -10_000.0,
                -10_000.0,
                TextParams {
                    font: Some(font),
                    font_size: 18,
                    font_scale: 1.0,
                    color: WHITE,
                    ..Default::default()
                },
            );
        }
    });
}

fn editor_font_raster_params(display_size: f32) -> (u16, f32) {
    let display_size = display_size.max(1.0);
    let raster_size = EDITOR_FONT_RASTER_TIERS
        .into_iter()
        .find(|size| *size as f32 >= display_size)
        .unwrap_or(*EDITOR_FONT_RASTER_TIERS.last().unwrap());
    let scale = display_size / raster_size as f32;
    (raster_size, scale)
}

pub(crate) fn editor_font_ready() -> bool {
    EDITOR_UI_FONT.with(|slot| slot.borrow().is_some())
}

fn editor_font_candidates() -> Vec<PathBuf> {
    let mut candidates = Vec::new();
    if let Some(windir) = std::env::var_os("WINDIR") {
        let fonts = Path::new(&windir).join("Fonts");
        // Segoe UI is the native Windows UI face. Arial is retained only as a
        // compatibility fallback for stripped-down Windows installations.
        candidates.push(fonts.join("segoeui.ttf"));
        candidates.push(fonts.join("segoeuisl.ttf"));
        candidates.push(fonts.join("arial.ttf"));
    }
    candidates
}

pub(crate) fn draw_editor_text(
    text: &str,
    x: f32,
    y: f32,
    font_size: f32,
    color: Color,
) -> TextDimensions {
    // Every text draw reasserts the shared UI material. Workspaces render
    // custom textures/materials and historically leaked that state across
    // panel switches, producing black text even though theme colors remained
    // correct. Text owns its material boundary; callers own the camera.
    gl_use_default_material();
    let display_size = (font_size * editor_text_scale()).max(1.0);
    let (raster_size, raster_scale) = editor_font_raster_params(display_size);
    EDITOR_UI_FONT.with(|slot| {
        let font = slot.borrow();
        if let Some(font) = font.as_ref() {
            draw_text_ex(
                text,
                x,
                y,
                TextParams {
                    font: Some(font),
                    font_size: raster_size,
                    font_scale: raster_scale,
                    color,
                    ..Default::default()
                },
            )
        } else {
            draw_text(text, x, y, display_size, color)
        }
    })
}

pub(crate) fn measure_editor_text(
    text: &str,
    _font: Option<&Font>,
    font_size: u16,
    font_scale: f32,
) -> TextDimensions {
    let display_size = ((font_size as f32) * editor_text_scale()).max(1.0);
    let (raster_size, raster_scale) = editor_font_raster_params(display_size);
    EDITOR_UI_FONT.with(|slot| {
        let font = slot.borrow();
        measure_text(text, font.as_ref(), raster_size, raster_scale * font_scale)
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn default_editor_text_scale_is_readable_without_being_layout_destructive() {
        assert!(DEFAULT_EDITOR_TEXT_SCALE >= 1.05);
        assert!(DEFAULT_EDITOR_TEXT_SCALE <= 1.25);
    }

    #[test]
    fn windows_font_candidates_never_depend_on_repository_font_files() {
        for path in editor_font_candidates() {
            let normalized = path
                .to_string_lossy()
                .replace('\\', "/")
                .to_ascii_lowercase();
            assert!(normalized.contains("/fonts/"));
            assert!(!normalized.contains("/content/"));
            assert!(!normalized.contains("/assets/"));
        }
    }

    #[test]
    fn raster_tiers_cover_editor_sizes_without_upscaling() {
        for requested in [9.0_f32, 12.0, 15.0, 18.0, 24.0, 30.0] {
            let display = requested * DEFAULT_EDITOR_TEXT_SCALE;
            let (raster, scale) = editor_font_raster_params(display);
            assert!(EDITOR_FONT_RASTER_TIERS.contains(&raster));
            assert!(scale > 0.0);
            assert!(scale <= 1.0);
        }
    }

    #[test]
    fn raster_tier_count_stays_bounded() {
        assert!(EDITOR_FONT_RASTER_TIERS.len() <= 6);
        assert_eq!(EDITOR_FONT_RASTER_TIERS, [14, 18, 24, 32, 40]);
    }

}
