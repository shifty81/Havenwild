use haven_world::water_surface::WaterDetailProfile;

/// Runtime-facing water render budget selected from camera scale and the
/// telemetry pressure state. V7 topology remains authoritative; this object
/// controls only visual subdivision and animation cadence.
#[derive(Debug, Clone, Copy, PartialEq)]
pub(crate) struct WaterRenderBudget {
    pub detail: WaterDetailProfile,
    pub animation_time: f32,
    pub pressure_active: bool,
}

impl WaterRenderBudget {
    pub(crate) fn select(camera_zoom: f32, pressure_active: bool, raw_time: f32) -> Self {
        let detail = WaterDetailProfile::for_camera_zoom(camera_zoom)
            .with_frame_pressure(camera_zoom, pressure_active);
        let animation_time = if detail.blend_layers <= 1 {
            (raw_time * 4.0).floor() * 0.25
        } else {
            raw_time
        };
        Self {
            detail,
            animation_time,
            pressure_active,
        }
    }

    pub(crate) const fn quality_label(self) -> &'static str {
        if self.pressure_active {
            "pressure"
        } else {
            "quality"
        }
    }

    pub(crate) const fn water_label(self) -> &'static str {
        self.detail.label()
    }

    pub(crate) const fn blend_layers(self) -> u8 {
        self.detail.blend_layers
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn normal_zoom_uses_emergency_single_layer_under_pressure() {
        let budget = WaterRenderBudget::select(1.0, true, 1.37);
        assert_eq!(budget.blend_layers(), 1);
        assert!(!budget.detail.draw_diagonal_corners);
        assert_eq!(budget.quality_label(), "pressure");
    }

    #[test]
    fn ultra_wide_animation_is_quantized() {
        let budget = WaterRenderBudget::select(0.45, false, 1.37);
        assert_eq!(budget.blend_layers(), 1);
        assert!((budget.animation_time - 1.25).abs() < f32::EPSILON);
    }

    #[test]
    fn balanced_animation_keeps_frame_time() {
        let budget = WaterRenderBudget::select(0.80, false, 1.37);
        assert_eq!(budget.blend_layers(), 2);
        assert!((budget.animation_time - 1.37).abs() < f32::EPSILON);
    }
}
