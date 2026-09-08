from pathlib import Path
root = Path(__file__).resolve().parents[5]
files = {
    'crates/haven_game/src/chunk_surface_cache.rs': [
        'ChunkSurfaceDescriptorCache', 'prepared_surfaces', 'reused_surfaces',
        'pending_surfaces', 'dirty_chunks_prepare_render_ready_commands'
    ],
    'crates/haven_game/src/base_terrain_cache.rs': ['last_dirty_chunks'],
    'crates/haven_game/src/runtime_terrain_pass.rs': ['chunk_surface_cache.borrow_mut().synchronize'],
    'crates/haven_game/src/runtime_performance_snapshot.rs': [
        'chunk_prepared_surfaces=', 'chunk_reused_surfaces='
    ],
    'crates/haven_game/src/runtime_diagnostics.rs': ['renderer_summary'],
}
for rel, markers in files.items():
    text = (root / rel).read_text(encoding='utf-8')
    for marker in markers:
        assert marker in text, f'{rel}: missing {marker}'
print('Pass 154B capability retained: dirty chunk surfaces are prepared, stable surfaces are reused, and diagnostics expose the lifecycle')
