use super::*;
use image::{imageops::FilterType, GenericImageView};
use std::collections::{HashMap, HashSet, VecDeque};
use std::path::Path;

/// Project-wide thumbnail runtime used by every file-backed asset browser.
///
/// The browser never uploads full source sheets to the GPU merely to display a
/// card. Large project atlases previously shared the editor GPU lifetime with
/// the dedicated UI font atlas and could create enough texture churn to revive
/// the intermittent black-glyph regression. Browser previews are now decoded
/// to a small CPU image first and only that bounded image becomes a GPU texture.
pub(crate) const UNIFIED_BROWSER_THUMBNAIL_EDGE: u32 = 96;
pub(crate) const UNIFIED_BROWSER_CACHE_LIMIT: usize = 96;
pub(crate) const UNIFIED_BROWSER_MAX_SOURCE_DIMENSION: u32 = 4096;
pub(crate) const UNIFIED_BROWSER_MAX_SOURCE_BYTES: u64 = 32 * 1024 * 1024;

#[derive(Default)]
pub(crate) struct UnifiedAssetBrowserRuntime {
    thumbnails: HashMap<String, Texture2D>,
    failures: HashSet<String>,
    insertion_order: VecDeque<String>,
    loads: u64,
    evictions: u64,
}

impl UnifiedAssetBrowserRuntime {
    pub(crate) fn clear(&mut self) {
        self.thumbnails.clear();
        self.failures.clear();
        self.insertion_order.clear();
    }

    pub(crate) fn contains_or_failed(&self, key: &str) -> bool {
        self.thumbnails.contains_key(key) || self.failures.contains(key)
    }

    pub(crate) fn texture(&self, key: &str) -> Option<&Texture2D> {
        self.thumbnails.get(key)
    }

    pub(crate) fn summary(&self) -> String {
        format!(
            "{} cached | {} skipped | {} loaded | {} evicted",
            self.thumbnails.len(),
            self.failures.len(),
            self.loads,
            self.evictions
        )
    }

    pub(crate) fn load_thumbnail(&mut self, key: String, path: &Path) -> Result<(), String> {
        if self.contains_or_failed(&key) {
            return Ok(());
        }
        match build_bounded_thumbnail(path) {
            Ok(texture) => {
                self.insert_texture(key, texture);
                self.loads = self.loads.saturating_add(1);
                Ok(())
            }
            Err(error) => {
                self.failures.insert(key);
                Err(error)
            }
        }
    }

    pub(crate) fn load_thumbnail_region(
        &mut self,
        key: String,
        path: &Path,
        source: Rect,
    ) -> Result<(), String> {
        if self.contains_or_failed(&key) {
            return Ok(());
        }
        match build_bounded_thumbnail_region(path, source) {
            Ok(texture) => {
                self.insert_texture(key, texture);
                self.loads = self.loads.saturating_add(1);
                Ok(())
            }
            Err(error) => {
                self.failures.insert(key);
                Err(error)
            }
        }
    }

    fn insert_texture(&mut self, key: String, texture: Texture2D) {
        while self.thumbnails.len() >= UNIFIED_BROWSER_CACHE_LIMIT {
            let Some(oldest) = self.insertion_order.pop_front() else {
                self.thumbnails.clear();
                break;
            };
            if self.thumbnails.remove(&oldest).is_some() {
                self.evictions = self.evictions.saturating_add(1);
            }
        }
        texture.set_filter(FilterMode::Nearest);
        self.insertion_order.push_back(key.clone());
        self.thumbnails.insert(key, texture);
    }
}


fn build_bounded_thumbnail_region(path: &Path, source: Rect) -> Result<Texture2D, String> {
    let metadata = std::fs::metadata(path)
        .map_err(|error| format!("thumbnail metadata {}: {error}", path.display()))?;
    if metadata.len() > UNIFIED_BROWSER_MAX_SOURCE_BYTES {
        return Err(format!("thumbnail source exceeds safety limit: {}", path.display()));
    }
    let image = image::open(path)
        .map_err(|error| format!("thumbnail decode {}: {error}", path.display()))?
        .to_rgba8();
    let x = source.x.max(0.0).floor() as u32;
    let y = source.y.max(0.0).floor() as u32;
    if x >= image.width() || y >= image.height() {
        return Err(format!("thumbnail crop begins outside source: {}", path.display()));
    }
    let width = (source.w.max(1.0).round() as u32).min(image.width() - x).max(1);
    let height = (source.h.max(1.0).round() as u32).min(image.height() - y).max(1);
    let cropped = image::imageops::crop_imm(&image, x, y, width, height).to_image();
    let scale = (UNIFIED_BROWSER_THUMBNAIL_EDGE as f32 / width as f32)
        .min(UNIFIED_BROWSER_THUMBNAIL_EDGE as f32 / height as f32)
        .min(1.0);
    let target_w = ((width as f32 * scale).round() as u32).max(1);
    let target_h = ((height as f32 * scale).round() as u32).max(1);
    let rgba = if target_w == width && target_h == height {
        cropped
    } else {
        image::imageops::resize(&cropped, target_w, target_h, FilterType::Nearest)
    };
    let texture = Texture2D::from_rgba8(rgba.width() as u16, rgba.height() as u16, rgba.as_raw());
    texture.set_filter(FilterMode::Nearest);
    Ok(texture)
}

fn build_bounded_thumbnail(path: &Path) -> Result<Texture2D, String> {
    let metadata = std::fs::metadata(path)
        .map_err(|error| format!("thumbnail metadata {}: {error}", path.display()))?;
    if metadata.len() > UNIFIED_BROWSER_MAX_SOURCE_BYTES {
        return Err(format!(
            "thumbnail source exceeds {} MiB safety limit: {}",
            UNIFIED_BROWSER_MAX_SOURCE_BYTES / 1024 / 1024,
            path.display()
        ));
    }

    let (source_w, source_h) = image::image_dimensions(path)
        .map_err(|error| format!("thumbnail dimensions {}: {error}", path.display()))?;
    if source_w == 0 || source_h == 0 {
        return Err(format!("thumbnail source has zero dimensions: {}", path.display()));
    }
    if source_w > UNIFIED_BROWSER_MAX_SOURCE_DIMENSION
        || source_h > UNIFIED_BROWSER_MAX_SOURCE_DIMENSION
    {
        return Err(format!(
            "thumbnail source {}x{} exceeds browser safety limit {}: {}",
            source_w,
            source_h,
            UNIFIED_BROWSER_MAX_SOURCE_DIMENSION,
            path.display()
        ));
    }

    let source = image::open(path)
        .map_err(|error| format!("thumbnail decode {}: {error}", path.display()))?;
    let (width, height) = source.dimensions();
    let scale = (UNIFIED_BROWSER_THUMBNAIL_EDGE as f32 / width.max(1) as f32)
        .min(UNIFIED_BROWSER_THUMBNAIL_EDGE as f32 / height.max(1) as f32)
        .min(1.0);
    let target_w = ((width as f32 * scale).round() as u32).max(1);
    let target_h = ((height as f32 * scale).round() as u32).max(1);
    let rgba = if target_w == width && target_h == height {
        source.to_rgba8()
    } else {
        source
            .resize(target_w, target_h, FilterType::Nearest)
            .to_rgba8()
    };
    let texture = Texture2D::from_rgba8(rgba.width() as u16, rgba.height() as u16, rgba.as_raw());
    texture.set_filter(FilterMode::Nearest);
    Ok(texture)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn thumbnail_budget_is_deliberately_small() {
        assert!(UNIFIED_BROWSER_THUMBNAIL_EDGE <= 128);
        assert!(UNIFIED_BROWSER_CACHE_LIMIT <= 128);
        let rgba_bytes = UNIFIED_BROWSER_THUMBNAIL_EDGE as usize
            * UNIFIED_BROWSER_THUMBNAIL_EDGE as usize
            * 4
            * UNIFIED_BROWSER_CACHE_LIMIT;
        assert!(rgba_bytes <= 8 * 1024 * 1024);
    }

    #[test]
    fn full_source_sheets_are_never_the_browser_gpu_contract() {
        assert!(UNIFIED_BROWSER_MAX_SOURCE_DIMENSION >= UNIFIED_BROWSER_THUMBNAIL_EDGE);
        assert!(UNIFIED_BROWSER_THUMBNAIL_EDGE < UNIFIED_BROWSER_MAX_SOURCE_DIMENSION);
    }
}
