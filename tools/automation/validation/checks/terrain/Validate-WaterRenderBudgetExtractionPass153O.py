from pathlib import Path
root = Path(__file__).resolve().parents[5]
required = {
    "crates/haven_game/src/water_render_budget.rs": [
        "struct WaterRenderBudget",
        "fn select",
        "fn quality_label",
        "fn water_label",
        "ultra_wide_animation_is_quantized",
    ],
    "crates/haven_game/src/render_telemetry.rs": ["fn water_budget"],
    "crates/haven_game/src/runtime_draw.rs": [".water_budget("],
    "crates/haven_game/src/runtime_diagnostics.rs": ["Pass 155B"],
    "crates/haven_game/src/runtime_terrain_pass.rs": [".water_budget(", "water_budget.animation_time"],
    "crates/haven_game/src/runtime_performance_snapshot.rs": ["PERF_SNAPSHOT pass=", "water_budget.quality_label()"],
    "crates/haven_game/src/main.rs": ["mod water_render_budget;"],
}
for relative, tokens in required.items():
    path = root / relative
    if not path.exists():
        raise SystemExit(f"Pass 153O missing {relative}")
    text = path.read_text(encoding="utf-8")
    for token in tokens:
        if token not in text:
            raise SystemExit(f"Pass 153O missing {token!r} in {relative}")

runtime_draw = root / "crates/haven_game/src/runtime_draw.rs"
line_count = len(runtime_draw.read_text(encoding="utf-8").splitlines())
if line_count > 750:
    raise SystemExit(f"Pass 153O runtime_draw.rs exceeds architecture ceiling: {line_count}")

for relative in [
    "crates/haven_game/src/runtime_draw.rs",
    "crates/haven_game/src/runtime_terrain_pass.rs",
]:
    text = (root / relative).read_text(encoding="utf-8")
    if "WaterDetailProfile::for_camera_zoom" in text:
        raise SystemExit(f"Pass 153O left direct water-budget selection in {relative}")

print("Pass 153O OK: water budget selection, labels, and animation cadence are centralized outside runtime frontends")
