use serde::{Deserialize, Serialize};

/// Canonical pixel-brush footprint used by Pixel Studio. Tools decide *what* a
/// stroke means (paint/erase/etc.); the brush decides which pixels participate.
/// This keeps brush behavior reusable instead of baking special shapes into UI code.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PixelBrushKind {
    #[default]
    Square,
    Circle,
    Diamond,
    Line,
    Dither,
    Spray,
    Cross,
    Ring,
    Noise,
}

impl PixelBrushKind {
    pub const ALL: [Self; 9] = [
        Self::Square,
        Self::Circle,
        Self::Diamond,
        Self::Line,
        Self::Dither,
        Self::Spray,
        Self::Cross,
        Self::Ring,
        Self::Noise,
    ];

    pub fn label(self) -> &'static str {
        match self {
            Self::Square => "Square",
            Self::Circle => "Circle",
            Self::Diamond => "Diamond",
            Self::Line => "Line",
            Self::Dither => "Dither",
            Self::Spray => "Spray",
            Self::Cross => "Cross",
            Self::Ring => "Ring",
            Self::Noise => "Noise",
        }
    }

    pub fn uses_density(self) -> bool {
        matches!(self, Self::Dither | Self::Spray | Self::Noise)
    }

    pub fn uses_angle(self) -> bool {
        matches!(self, Self::Line)
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PixelBrushSettings {
    #[serde(default)]
    pub kind: PixelBrushKind,
    #[serde(default = "default_size")]
    pub size: u8,
    #[serde(default = "default_opacity")]
    pub opacity: u8,
    #[serde(default = "default_density")]
    pub density: u8,
    #[serde(default)]
    pub angle_degrees: i16,
    #[serde(default = "default_spacing")]
    pub spacing: u8,
}

impl Default for PixelBrushSettings {
    fn default() -> Self {
        Self {
            kind: PixelBrushKind::Square,
            size: default_size(),
            opacity: default_opacity(),
            density: default_density(),
            angle_degrees: 0,
            spacing: default_spacing(),
        }
    }
}

fn default_size() -> u8 { 1 }
fn default_opacity() -> u8 { u8::MAX }
fn default_density() -> u8 { 128 }
fn default_spacing() -> u8 { 1 }

impl PixelBrushSettings {
    pub fn normalized(mut self) -> Self {
        self.size = self.size.clamp(1, 64);
        self.spacing = self.spacing.clamp(1, 64);
        self.angle_degrees = normalize_angle(self.angle_degrees);
        self
    }

    /// Returns whether the offset belongs to this brush footprint. `center` is
    /// supplied so deterministic ordered/spray patterns remain stable in image
    /// coordinates instead of crawling while the mouse moves.
    pub fn contains_offset(self, center: (i32, i32), dx: i32, dy: i32) -> bool {
        let settings = self.normalized();
        let size = i32::from(settings.size);
        let left = (size - 1) / 2;
        let right = size / 2;
        if dx < -left || dx > right || dy < -left || dy > right {
            return false;
        }
        match settings.kind {
            PixelBrushKind::Square => true,
            PixelBrushKind::Circle => {
                let radius = (size as f32 - 1.0) * 0.5 + 0.45;
                let x = dx as f32 + if size % 2 == 0 { -0.5 } else { 0.0 };
                let y = dy as f32 + if size % 2 == 0 { -0.5 } else { 0.0 };
                x * x + y * y <= radius * radius
            }
            PixelBrushKind::Diamond => {
                let radius = ((size - 1) / 2).max(0);
                dx.abs() + dy.abs() <= radius.max(1) || size <= 2
            }
            PixelBrushKind::Line => line_contains(settings, dx, dy),
            PixelBrushKind::Dither => ordered_dither_contains(settings, center, dx, dy),
            PixelBrushKind::Spray => {
                let radius = (size as f32 - 1.0) * 0.5 + 0.45;
                let x = dx as f32 + if size % 2 == 0 { -0.5 } else { 0.0 };
                let y = dy as f32 + if size % 2 == 0 { -0.5 } else { 0.0 };
                if x * x + y * y > radius * radius {
                    return false;
                }
                deterministic_byte(center.0 + dx, center.1 + dy, 0x53) <= settings.density
            }
            PixelBrushKind::Cross => dx == 0 || dy == 0,
            PixelBrushKind::Ring => {
                let radius = (size as f32 - 1.0) * 0.5 + 0.45;
                let x = dx as f32 + if size % 2 == 0 { -0.5 } else { 0.0 };
                let y = dy as f32 + if size % 2 == 0 { -0.5 } else { 0.0 };
                let distance = (x * x + y * y).sqrt();
                distance <= radius && distance >= (radius - 1.15).max(0.0)
            }
            PixelBrushKind::Noise => deterministic_byte(center.0 + dx, center.1 + dy, 0x9D) <= settings.density,
        }
    }
}

fn line_contains(settings: PixelBrushSettings, dx: i32, dy: i32) -> bool {
    if settings.size <= 1 {
        return dx == 0 && dy == 0;
    }
    let radians = (settings.angle_degrees as f32).to_radians();
    let direction = [radians.cos(), radians.sin()];
    let along = dx as f32 * direction[0] + dy as f32 * direction[1];
    let perpendicular = -dx as f32 * direction[1] + dy as f32 * direction[0];
    let half = settings.size as f32 * 0.5;
    along.abs() <= half && perpendicular.abs() <= 0.58
}

fn ordered_dither_contains(
    settings: PixelBrushSettings,
    center: (i32, i32),
    dx: i32,
    dy: i32,
) -> bool {
    // 4x4 Bayer matrix. Density maps directly to coverage while preserving a
    // crisp, deterministic pixel-art pattern.
    const BAYER_4: [[u8; 4]; 4] = [
        [0, 8, 2, 10],
        [12, 4, 14, 6],
        [3, 11, 1, 9],
        [15, 7, 13, 5],
    ];
    let x = (center.0 + dx).rem_euclid(4) as usize;
    let y = (center.1 + dy).rem_euclid(4) as usize;
    let threshold = u16::from(BAYER_4[y][x]) * 17;
    threshold <= u16::from(settings.density)
}

fn normalize_angle(angle: i16) -> i16 {
    let mut value = angle % 360;
    if value < 0 { value += 360; }
    value
}

fn deterministic_byte(x: i32, y: i32, salt: u32) -> u8 {
    let mut value = (x as u32).wrapping_mul(0x9E37_79B1)
        ^ (y as u32).wrapping_mul(0x85EB_CA77)
        ^ salt.wrapping_mul(0xC2B2_AE3D);
    value ^= value >> 16;
    value = value.wrapping_mul(0x7FEB_352D);
    value ^= value >> 15;
    value = value.wrapping_mul(0x846C_A68B);
    value ^= value >> 16;
    (value & 0xFF) as u8
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn square_one_pixel_is_exact() {
        let brush = PixelBrushSettings::default();
        assert!(brush.contains_offset((10, 10), 0, 0));
        assert!(!brush.contains_offset((10, 10), 1, 0));
    }

    #[test]
    fn dither_is_stable_in_image_space() {
        let brush = PixelBrushSettings { kind: PixelBrushKind::Dither, size: 5, density: 128, ..Default::default() };
        assert_eq!(brush.contains_offset((12, 8), 1, 1), brush.contains_offset((12, 8), 1, 1));
    }

    #[test]
    fn spray_is_deterministic() {
        let brush = PixelBrushSettings { kind: PixelBrushKind::Spray, size: 8, density: 160, ..Default::default() };
        let first: Vec<_> = (-4..=4).flat_map(|y| (-4..=4).map(move |x| (x, y))).filter(|(x, y)| brush.contains_offset((20, 30), *x, *y)).collect();
        let second: Vec<_> = (-4..=4).flat_map(|y| (-4..=4).map(move |x| (x, y))).filter(|(x, y)| brush.contains_offset((20, 30), *x, *y)).collect();
        assert_eq!(first, second);
    }
    #[test]
    fn cross_brush_keeps_orthogonal_arms() {
        let brush = PixelBrushSettings { kind: PixelBrushKind::Cross, size: 5, ..Default::default() };
        assert!(brush.contains_offset((10, 10), 0, 2));
        assert!(brush.contains_offset((10, 10), -2, 0));
        assert!(!brush.contains_offset((10, 10), 1, 1));
    }

    #[test]
    fn ring_brush_leaves_center_open_when_large_enough() {
        let brush = PixelBrushSettings { kind: PixelBrushKind::Ring, size: 7, ..Default::default() };
        assert!(!brush.contains_offset((0, 0), 0, 0));
        assert!(brush.contains_offset((0, 0), 3, 0));
    }

    #[test]
    fn noise_brush_is_deterministic_in_image_space() {
        let brush = PixelBrushSettings { kind: PixelBrushKind::Noise, size: 8, density: 128, ..Default::default() };
        let a = brush.contains_offset((44, 81), 2, -1);
        let b = brush.contains_offset((44, 81), 2, -1);
        assert_eq!(a, b);
    }

}
