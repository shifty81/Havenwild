use std::cell::Cell;

const FRAME_SMOOTHING_ALPHA: f64 = 1.0 / 120.0;
const SNAPSHOT_INTERVAL_SECONDS: f64 = 5.0;
const PRESSURE_ENTER_WALL_MICROS: u64 = 25_000;
const PRESSURE_EXIT_WALL_MICROS: u64 = 20_000;
const PRESSURE_ENTER_FRAMES: u16 = 90;
const PRESSURE_EXIT_FRAMES: u16 = 180;

#[derive(Default)]
pub(crate) struct TerrainRenderTelemetry {
    visible_cells: Cell<usize>,
    visible_chunks: Cell<usize>,
    retained_chunks: Cell<usize>,
    base_cache_rebuilt_chunks: Cell<usize>,
    base_cache_rebuilt_cells: Cell<usize>,
    visible_cache_hits: Cell<u64>,
    visible_cache_rebuilds: Cell<u64>,
    visible_cache_cells: Cell<usize>,
    visible_cache_reason: Cell<&'static str>,
    transition_cells: Cell<usize>,
    estimated_water_primitives: Cell<usize>,
    water_shader_submissions: Cell<usize>,
    preparation_micros: Cell<u64>,
    update_micros: Cell<u64>,
    draw_micros: Cell<u64>,
    submitted_frame_micros: Cell<u64>,
    smoothed_frame_micros: Cell<u64>,
    wall_frame_micros: Cell<u64>,
    presentation_gap_micros: Cell<u64>,
    smoothed_wall_frame_micros: Cell<u64>,
    profiled_frames: Cell<u64>,
    next_snapshot_at: Cell<f64>,
    pressure_frames: Cell<u16>,
    recovery_frames: Cell<u16>,
    adaptive_pressure: Cell<bool>,
}

impl TerrainRenderTelemetry {
    #[allow(clippy::too_many_arguments)]
    pub(crate) fn record(
        &self,
        visible_cells: usize,
        visible_chunks: usize,
        retained_chunks: usize,
        base_cache_rebuilt_chunks: usize,
        base_cache_rebuilt_cells: usize,
        visible_cache_hits: u64,
        visible_cache_rebuilds: u64,
        visible_cache_cells: usize,
        visible_cache_reason: &'static str,
        transition_cells: usize,
        estimated_water_primitives: usize,
        water_shader_submissions: usize,
        preparation_seconds: f64,
    ) {
        self.visible_cells.set(visible_cells);
        self.visible_chunks.set(visible_chunks);
        self.retained_chunks.set(retained_chunks);
        self.base_cache_rebuilt_chunks
            .set(base_cache_rebuilt_chunks);
        self.base_cache_rebuilt_cells.set(base_cache_rebuilt_cells);
        self.visible_cache_hits.set(visible_cache_hits);
        self.visible_cache_rebuilds.set(visible_cache_rebuilds);
        self.visible_cache_cells.set(visible_cache_cells);
        self.visible_cache_reason.set(visible_cache_reason);
        self.transition_cells.set(transition_cells);
        self.estimated_water_primitives
            .set(estimated_water_primitives);
        self.water_shader_submissions.set(water_shader_submissions);
        self.preparation_micros
            .set(seconds_to_micros(preparation_seconds));
    }

    pub(crate) fn record_frame_cpu(
        &self,
        update_seconds: f64,
        draw_seconds: f64,
        submitted_frame_seconds: f64,
        wall_frame_seconds: f64,
    ) {
        let frame_micros = seconds_to_micros(submitted_frame_seconds);
        self.update_micros.set(seconds_to_micros(update_seconds));
        self.draw_micros.set(seconds_to_micros(draw_seconds));
        self.submitted_frame_micros.set(frame_micros);
        let wall_micros = seconds_to_micros(wall_frame_seconds);
        self.wall_frame_micros.set(wall_micros);
        self.presentation_gap_micros
            .set(wall_micros.saturating_sub(frame_micros));

        let frames = self.profiled_frames.get();
        let smoothed = if frames == 0 {
            frame_micros
        } else {
            let previous = self.smoothed_frame_micros.get() as f64;
            (previous + (frame_micros as f64 - previous) * FRAME_SMOOTHING_ALPHA) as u64
        };
        self.smoothed_frame_micros.set(smoothed);
        let smoothed_wall = if frames == 0 {
            wall_micros
        } else {
            let previous = self.smoothed_wall_frame_micros.get() as f64;
            (previous + (wall_micros as f64 - previous) * FRAME_SMOOTHING_ALPHA) as u64
        };
        self.smoothed_wall_frame_micros.set(smoothed_wall);
        self.profiled_frames.set(frames.saturating_add(1));
        self.update_adaptive_pressure(smoothed_wall);
    }

    fn update_adaptive_pressure(&self, smoothed_wall_micros: u64) {
        if self.adaptive_pressure.get() {
            if smoothed_wall_micros <= PRESSURE_EXIT_WALL_MICROS {
                let recovery = self.recovery_frames.get().saturating_add(1);
                self.recovery_frames.set(recovery);
                if recovery >= PRESSURE_EXIT_FRAMES {
                    self.adaptive_pressure.set(false);
                    self.recovery_frames.set(0);
                    self.pressure_frames.set(0);
                }
            } else {
                self.recovery_frames.set(0);
            }
            return;
        }

        if smoothed_wall_micros >= PRESSURE_ENTER_WALL_MICROS {
            let pressure = self.pressure_frames.get().saturating_add(1);
            self.pressure_frames.set(pressure);
            if pressure >= PRESSURE_ENTER_FRAMES {
                self.adaptive_pressure.set(true);
                self.pressure_frames.set(0);
                self.recovery_frames.set(0);
            }
        } else {
            self.pressure_frames.set(0);
        }
    }

    pub(crate) fn visible_cells(&self) -> usize {
        self.visible_cells.get()
    }

    pub(crate) fn visible_chunks(&self) -> usize {
        self.visible_chunks.get()
    }

    pub(crate) fn retained_chunks(&self) -> usize {
        self.retained_chunks.get()
    }

    pub(crate) fn base_cache_rebuilt_chunks(&self) -> usize {
        self.base_cache_rebuilt_chunks.get()
    }

    pub(crate) fn base_cache_rebuilt_cells(&self) -> usize {
        self.base_cache_rebuilt_cells.get()
    }

    pub(crate) fn visible_cache_hits(&self) -> u64 {
        self.visible_cache_hits.get()
    }
    pub(crate) fn visible_cache_rebuilds(&self) -> u64 {
        self.visible_cache_rebuilds.get()
    }
    pub(crate) fn visible_cache_cells(&self) -> usize {
        self.visible_cache_cells.get()
    }
    pub(crate) fn visible_cache_reason(&self) -> &'static str {
        self.visible_cache_reason.get()
    }

    pub(crate) fn chunk_summary(&self) -> String {
        format!(
            "{}/{} chunks / {}+{} base rebuilt",
            self.visible_chunks(),
            self.retained_chunks(),
            self.base_cache_rebuilt_chunks(),
            self.base_cache_rebuilt_cells(),
        )
    }

    pub(crate) fn transition_cells(&self) -> usize {
        self.transition_cells.get()
    }

    pub(crate) fn estimated_water_primitives(&self) -> usize {
        self.estimated_water_primitives.get()
    }

    pub(crate) fn water_shader_submissions(&self) -> usize {
        self.water_shader_submissions.get()
    }

    pub(crate) fn preparation_millis(&self) -> f32 {
        micros_to_millis(self.preparation_micros.get())
    }

    pub(crate) fn update_millis(&self) -> f32 {
        micros_to_millis(self.update_micros.get())
    }

    pub(crate) fn draw_millis(&self) -> f32 {
        micros_to_millis(self.draw_micros.get())
    }

    pub(crate) fn submitted_frame_millis(&self) -> f32 {
        micros_to_millis(self.submitted_frame_micros.get())
    }

    pub(crate) fn smoothed_frame_millis(&self) -> f32 {
        micros_to_millis(self.smoothed_frame_micros.get())
    }

    pub(crate) fn wall_frame_millis(&self) -> f32 {
        micros_to_millis(self.wall_frame_micros.get())
    }

    pub(crate) fn presentation_gap_millis(&self) -> f32 {
        micros_to_millis(self.presentation_gap_micros.get())
    }

    pub(crate) fn smoothed_wall_frame_millis(&self) -> f32 {
        micros_to_millis(self.smoothed_wall_frame_micros.get())
    }

    pub(crate) fn should_emit_snapshot(&self, now: f64) -> bool {
        let next = self.next_snapshot_at.get();
        if now < next {
            return false;
        }
        self.next_snapshot_at.set(now + SNAPSHOT_INTERVAL_SECONDS);
        true
    }

    pub(crate) fn estimated_fps(&self) -> f32 {
        let wall_ms = self.smoothed_wall_frame_millis();
        if wall_ms <= f32::EPSILON {
            0.0
        } else {
            1000.0 / wall_ms
        }
    }

    pub(crate) fn adaptive_pressure_active(&self) -> bool {
        self.adaptive_pressure.get()
    }

    pub(crate) fn water_budget(
        &self,
        camera_zoom: f32,
        raw_time: f32,
    ) -> crate::water_render_budget::WaterRenderBudget {
        crate::water_render_budget::WaterRenderBudget::select(
            camera_zoom,
            self.adaptive_pressure_active(),
            raw_time,
        )
    }

    pub(crate) fn bottleneck_label(&self) -> &'static str {
        let wall = self.wall_frame_micros.get();
        let cpu = self.submitted_frame_micros.get();
        if wall == 0 {
            "warming"
        } else if cpu.saturating_mul(100) >= wall.saturating_mul(80) {
            "cpu-submit"
        } else {
            "gpu/present"
        }
    }
}

fn seconds_to_micros(seconds: f64) -> u64 {
    (seconds.max(0.0) * 1_000_000.0) as u64
}

fn micros_to_millis(micros: u64) -> f32 {
    micros as f32 / 1000.0
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn frame_profile_records_independent_update_and_draw_costs() {
        let telemetry = TerrainRenderTelemetry::default();
        telemetry.record_frame_cpu(0.0015, 0.0045, 0.0062, 0.0167);
        assert!((telemetry.update_millis() - 1.5).abs() < 0.01);
        assert!((telemetry.draw_millis() - 4.5).abs() < 0.01);
        assert!((telemetry.submitted_frame_millis() - 6.2).abs() < 0.01);
        assert!((telemetry.smoothed_frame_millis() - 6.2).abs() < 0.01);
        assert!((telemetry.wall_frame_millis() - 16.7).abs() < 0.01);
        assert!((telemetry.presentation_gap_millis() - 10.5).abs() < 0.01);
        assert_eq!(telemetry.bottleneck_label(), "gpu/present");
        assert!((telemetry.estimated_fps() - 59.88).abs() < 0.2);
    }

    #[test]
    fn sustained_slow_frames_enable_adaptive_pressure() {
        let telemetry = TerrainRenderTelemetry::default();
        for _ in 0..PRESSURE_ENTER_FRAMES {
            telemetry.record_frame_cpu(0.001, 0.004, 0.006, 0.030);
        }
        assert!(telemetry.adaptive_pressure_active());
    }

    #[test]
    fn snapshot_interval_prevents_per_frame_log_spam() {
        let telemetry = TerrainRenderTelemetry::default();
        assert!(telemetry.should_emit_snapshot(10.0));
        assert!(!telemetry.should_emit_snapshot(12.0));
        assert!(telemetry.should_emit_snapshot(15.0));
    }

    #[test]
    fn frame_profile_smooths_spikes_instead_of_replacing_average() {
        let telemetry = TerrainRenderTelemetry::default();
        telemetry.record_frame_cpu(0.001, 0.003, 0.004, 0.016);
        telemetry.record_frame_cpu(0.010, 0.030, 0.040, 0.050);
        assert!(telemetry.smoothed_frame_millis() > 4.0);
        assert!(telemetry.smoothed_frame_millis() < 10.0);
    }
}
