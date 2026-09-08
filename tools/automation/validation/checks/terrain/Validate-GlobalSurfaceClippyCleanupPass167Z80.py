#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]


def main() -> int:
    main_rs = (ROOT / "crates/haven_game/src/main.rs").read_text(encoding="utf-8-sig")
    start = main_rs.index("use haven_assets::lpc_mapped_terrain::{")
    end = main_rs.index("};", start)
    import_block = main_rs[start:end]
    assert "lpc_mapped_terrain_runtime_entry_for_tile_sampler" in import_block
    assert "lpc_mapped_terrain_transition_entry_for_tile_sampler" in import_block
    assert "lpc_mapped_terrain_runtime_entry_for_map" not in import_block
    assert "lpc_mapped_terrain_transition_entry_for_map" not in import_block

    mapped = (
        (ROOT / "crates/haven_assets/src/lpc_mapped_terrain.rs").read_text(encoding="utf-8-sig")
        + "\n"
        + (ROOT / "crates/haven_assets/src/lpc_mapped_terrain/sampling.rs").read_text(encoding="utf-8-sig")
        + "\n"
        + (ROOT / "crates/haven_assets/src/lpc_mapped_terrain/tests.rs").read_text(encoding="utf-8-sig")
    )
    assert "Some(if x < haven_core::MAP_W as i32 {" in mapped
    assert "Some(if x <= haven_core::MAP_W as i32 - 1 {" not in mapped
    assert "global_sampler_resolves_authored_tuple_across_storage_partition_edge" in mapped

    print("Pass167Z80 global surface Clippy cleanup validated")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
