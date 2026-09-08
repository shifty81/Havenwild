use image::RgbaImage;
use serde::Deserialize;
use std::{fs, path::Path};

pub(crate) const COLLISION_OVERRIDE_REGISTRY_PATH: &str =
    "content/world/collision_overrides_v1.json";

#[derive(Clone, Debug, Default, Deserialize)]
#[serde(rename_all = "camelCase")]
struct RegistryFile {
    #[allow(dead_code)]
    schema: String,
    #[serde(default)]
    entries: Vec<RegistryEntry>,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct RegistryEntry {
    scene_id: String,
    local_rect: [i32; 4],
    #[allow(dead_code)]
    revision: String,
    add_mask: String,
    subtract_mask: String,
}

#[derive(Clone, Debug)]
struct LoadedCollisionOverride {
    scene_id: String,
    local_rect: [i32; 4],
    add: Option<RgbaImage>,
    subtract: Option<RgbaImage>,
}

#[derive(Clone, Debug, Default)]
pub(crate) struct RuntimeCollisionOverrideRegistry {
    entries: Vec<LoadedCollisionOverride>,
}

impl RuntimeCollisionOverrideRegistry {
    pub(crate) fn load(root: &Path) -> Result<Self, String> {
        let path = root.join(COLLISION_OVERRIDE_REGISTRY_PATH);
        if !path.exists() {
            return Ok(Self::default());
        }
        let text = fs::read_to_string(&path)
            .map_err(|error| format!("collision override registry read failed: {error}"))?;
        let file: RegistryFile = serde_json::from_str(&text)
            .map_err(|error| format!("collision override registry parse failed: {error}"))?;
        let mut entries = Vec::new();
        for entry in file.entries {
            let add = load_mask(root, &entry.add_mask);
            let subtract = load_mask(root, &entry.subtract_mask);
            entries.push(LoadedCollisionOverride {
                scene_id: entry.scene_id,
                local_rect: entry.local_rect,
                add,
                subtract,
            });
        }
        Ok(Self { entries })
    }

    /// Resolve one player-space point against authored sub-tile collision. Subtract wins
    /// over the pre-existing tile/building result, Add blocks otherwise, and transparent
    /// pixels preserve the current gameplay collision authority.
    pub(crate) fn allows_position(
        &self,
        scene_id: &str,
        local_x_px: f32,
        local_y_px: f32,
        base_allowed: bool,
    ) -> bool {
        let mut allowed = base_allowed;
        for entry in self.entries.iter().filter(|entry| entry.scene_id == scene_id) {
            let [x, y, w, h] = entry.local_rect;
            let px = local_x_px.floor() as i32 - x * 32;
            let py = local_y_px.floor() as i32 - y * 32;
            if px < 0 || py < 0 || px >= w * 32 || py >= h * 32 { continue; }
            if mask_hit(entry.subtract.as_ref(), px as u32, py as u32) {
                allowed = true;
                continue;
            }
            if mask_hit(entry.add.as_ref(), px as u32, py as u32) {
                allowed = false;
            }
        }
        allowed
    }

    pub(crate) fn len(&self) -> usize { self.entries.len() }
}

fn load_mask(root: &Path, relative: &str) -> Option<RgbaImage> {
    if relative.trim().is_empty() { return None; }
    image::open(root.join(relative)).ok().map(|image| image.to_rgba8())
}

fn mask_hit(mask: Option<&RgbaImage>, x: u32, y: u32) -> bool {
    mask.and_then(|image| (x < image.width() && y < image.height()).then(|| image.get_pixel(x, y).0[3] != 0)).unwrap_or(false)
}

#[cfg(test)]
mod tests {
    use super::*;
    use image::Rgba;

    #[test]
    fn subtract_can_open_base_collision_and_add_can_block_open_space() {
        let mut add = RgbaImage::new(32, 32);
        let mut subtract = RgbaImage::new(32, 32);
        add.put_pixel(4, 4, Rgba([255, 255, 255, 255]));
        subtract.put_pixel(8, 8, Rgba([255, 255, 255, 255]));
        let registry = RuntimeCollisionOverrideRegistry {
            entries: vec![LoadedCollisionOverride {
                scene_id: "estate".to_string(),
                local_rect: [10, 20, 1, 1],
                add: Some(add),
                subtract: Some(subtract),
            }],
        };
        assert!(!registry.allows_position("estate", 10.0 * 32.0 + 4.0, 20.0 * 32.0 + 4.0, true));
        assert!(registry.allows_position("estate", 10.0 * 32.0 + 8.0, 20.0 * 32.0 + 8.0, false));
        assert!(registry.allows_position("estate", 10.0 * 32.0 + 12.0, 20.0 * 32.0 + 12.0, true));
    }
}
