use super::*;

pub(crate) fn format_performance_snapshot(game: &Game, now: f64) -> String {
    let water_budget = game
        .terrain_render_telemetry
        .water_budget(game.camera_zoom, now as f32);
    let water_detail = water_budget.detail;
    let cache_report = game.terrain_cache.last_report();
    let chunk = game.base_terrain_cache.borrow();
    let capability = chunk.render_capability();
    let lifecycle = chunk.surface_lifecycle_report();
    let surface_cache = game.chunk_surface_cache.borrow();
    let surfaces = surface_cache.last_report();
    let execution = surface_cache.last_execution();
    let (scene_surface_active, scene_surface_rebuilds, scene_surface_draws) =
        game.terrain_scene_surface.borrow().telemetry();
    format!(
        "PERF_SNAPSHOT pass=167Z30 fps={:.1} zoom={:.3} water={} layers={} budget={} visible={} visible_chunks={} retained_chunks={} base_rebuilt_chunks={} base_rebuilt_cells={} plan_cells={} plan_hits={} plan_rebuilds={} plan_reason={} chunk_backend={} chunk_capability={} chunk_dirty_surfaces={} chunk_invalidation={} chunk_prepared_surfaces={} chunk_reused_surfaces={} chunk_pending_surfaces={} chunk_total_surfaces={} chunk_prepared_commands={} chunk_retained_commands={} chunk_exec_requested={} chunk_exec_active={} chunk_exec_visible_surfaces={} chunk_exec_commands={} chunk_exec_fallbacks={} chunk_exec_expected={} chunk_exec_unique={} chunk_exec_duplicates={} chunk_exec_missing={} chunk_exec_unexpected={} chunk_exec_parity_ok={} chunk_exec_parity_mismatches={} chunk_exec_reason={} transitions={} water_primitives={} water_submissions={} prep_ms={:.2} update_ms={:.2} draw_ms={:.2} cpu_ms={:.2} cpu_avg_ms={:.2} wall_ms={:.2} wall_avg_ms={:.2} present_ms={:.2} bottleneck={} water_masks={} cache_rebuilt={} scene_surface_active={} scene_surface_rebuilds={} scene_surface_draws={}",
        game.terrain_render_telemetry.estimated_fps(),
        game.camera_zoom,
        water_detail.label(),
        water_detail.blend_layers,
        water_budget.quality_label(),
        game.terrain_render_telemetry.visible_cells(),
        game.terrain_render_telemetry.visible_chunks(),
        game.terrain_render_telemetry.retained_chunks(),
        game.terrain_render_telemetry.base_cache_rebuilt_chunks(),
        game.terrain_render_telemetry.base_cache_rebuilt_cells(),
        game.terrain_render_telemetry.visible_cache_cells(),
        game.terrain_render_telemetry.visible_cache_hits(),
        game.terrain_render_telemetry.visible_cache_rebuilds(),
        game.terrain_render_telemetry.visible_cache_reason(),
        capability.backend_label(),
        capability.capability_label(),
        lifecycle.dirty_surfaces,
        lifecycle.reason_label(),
        surfaces.prepared_surfaces,
        surfaces.reused_surfaces,
        surfaces.pending_surfaces,
        surfaces.total_surfaces,
        surfaces.prepared_commands,
        surfaces.retained_commands,
        execution.requested,
        execution.active,
        execution.visible_surfaces,
        execution.executed_commands,
        execution.fallback_count,
        execution.expected_commands,
        execution.unique_commands,
        execution.duplicate_commands,
        execution.missing_coordinates,
        execution.unexpected_coordinates,
        execution.parity_ok,
        execution.parity_mismatches,
        execution.reason,
        game.terrain_render_telemetry.transition_cells(),
        game.terrain_render_telemetry.estimated_water_primitives(),
        game.terrain_render_telemetry.water_shader_submissions(),
        game.terrain_render_telemetry.preparation_millis(),
        game.terrain_render_telemetry.update_millis(),
        game.terrain_render_telemetry.draw_millis(),
        game.terrain_render_telemetry.submitted_frame_millis(),
        game.terrain_render_telemetry.smoothed_frame_millis(),
        game.terrain_render_telemetry.wall_frame_millis(),
        game.terrain_render_telemetry.smoothed_wall_frame_millis(),
        game.terrain_render_telemetry.presentation_gap_millis(),
        game.terrain_render_telemetry.bottleneck_label(),
        cache_report.water_mask_cells,
        cache_report.recalculated_cells,
        scene_surface_active,
        scene_surface_rebuilds,
        scene_surface_draws,
    )
}
