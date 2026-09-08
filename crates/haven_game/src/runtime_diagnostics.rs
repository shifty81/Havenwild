pub(crate) struct RuntimeDiagnosticsLine<'a> {
    pub generation: u32,
    pub water_label: &'a str,
    pub water_layers: usize,
    pub quality_label: &'a str,
    pub water_masks: usize,
    pub cache_rebuilt: usize,
    pub visible_cells: usize,
    pub chunk_summary: &'a str,
    pub traversal_summary: &'a str,
    pub renderer_summary: &'a str,
    pub transition_cells: usize,
    pub water_primitives: usize,
    pub prep_ms: f32,
    pub update_ms: f32,
    pub draw_ms: f32,
    pub cpu_ms: f32,
    pub cpu_avg_ms: f32,
    pub wall_ms: f32,
    pub wall_avg_ms: f32,
    pub present_ms: f32,
    pub bottleneck: &'a str,
    pub mounted_packs: usize,
    pub render_bindings: usize,
    pub fallback_bindings: usize,
    pub resources: usize,
}

pub(crate) fn format_runtime_diagnostics(line: RuntimeDiagnosticsLine<'_>) -> String {
    format!(
        "Pass 167Z109W15B | cliff authority Pass 167Z109W14: demo-grounded c2/c1/c3 south cliff grammar + literal same-delta face height + diagonal low-side projection + clean authored rims + one-tile cave mouths + authored ramps + V7 surfaces | Gen {} | Water {} ({} layers, {}) | cache {} masks / {} rebuilt | terrain {} visible in {} / frame-plan {} / renderer {} / {} transition / ~{} water prim / {:.2} ms prep | frame {:.2} ms update + {:.2} ms draw = {:.2} ms cpu ({:.2} ms avg) | wall {:.2} ms ({:.2} avg), {:.2} ms present [{}] | Assets: {} packs | {} render bindings ({} fallback) | {} resources",
        line.generation,
        line.water_label,
        line.water_layers,
        line.quality_label,
        line.water_masks,
        line.cache_rebuilt,
        line.visible_cells,
        line.chunk_summary,
        line.traversal_summary,
        line.renderer_summary,
        line.transition_cells,
        line.water_primitives,
        line.prep_ms,
        line.update_ms,
        line.draw_ms,
        line.cpu_ms,
        line.cpu_avg_ms,
        line.wall_ms,
        line.wall_avg_ms,
        line.present_ms,
        line.bottleneck,
        line.mounted_packs,
        line.render_bindings,
        line.fallback_bindings,
        line.resources,
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn formats_current_pass_and_chunk_diagnostics() {
        let text = format_runtime_diagnostics(RuntimeDiagnosticsLine {
            generation: 6,
            water_label: "wide",
            water_layers: 1,
            quality_label: "pressure",
            water_masks: 12,
            cache_rebuilt: 0,
            visible_cells: 256,
            chunk_summary: "4/16 chunks / 0+0 base rebuilt",
            traversal_summary: "12 cells / 44 hits / 2 rebuilds / hit",
            renderer_summary: "per-tile-fallback / descriptor-ready / 0 dirty / stable",
            transition_cells: 8,
            water_primitives: 8,
            prep_ms: 0.2,
            update_ms: 1.0,
            draw_ms: 4.0,
            cpu_ms: 5.0,
            cpu_avg_ms: 5.2,
            wall_ms: 16.7,
            wall_avg_ms: 16.8,
            present_ms: 11.7,
            bottleneck: "gpu/present",
            mounted_packs: 2,
            render_bindings: 10,
            fallback_bindings: 1,
            resources: 20,
        });
        assert!(text.contains("Pass 167Z109W15B"));
        assert!(text.contains("Pass 167Z109W14"));
        assert!(text.contains("44 hits"));
        assert!(text.contains("frame-plan"));
        assert!(text.contains("4/16 chunks"));
        assert!(text.contains("per-tile-fallback"));
    }
}
