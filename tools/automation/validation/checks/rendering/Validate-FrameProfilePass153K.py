from pathlib import Path

root = Path(__file__).resolve().parents[3]
telemetry = (root / "crates/haven_game/src/render_telemetry.rs").read_text(encoding="utf-8")
entry = (root / "crates/haven_game/src/client_entry.rs").read_text(encoding="utf-8")
diagnostics = (root / "crates/haven_game/src/runtime_diagnostics.rs").read_text(encoding="utf-8")

required_telemetry = [
    "record_frame_cpu",
    "update_millis",
    "draw_millis",
    "submitted_frame_millis",
    "smoothed_frame_millis",
    "FRAME_SMOOTHING_ALPHA",
]
missing = [token for token in required_telemetry if token not in telemetry]
if missing:
    raise SystemExit(f"Pass 153K telemetry missing: {missing}")
if "submitted_frame_started_at" not in entry or "record_frame_cpu" not in entry:
    raise SystemExit("Pass 153K client loop does not record whole-frame CPU timing")
required_diagnostics = ["V7 authority", "ms update", "ms draw", "ms cpu", "ms present", "update_ms", "draw_ms", "cpu_ms", "present_ms"]
missing_diagnostics = [token for token in required_diagnostics if token not in diagnostics]
if missing_diagnostics:
    raise SystemExit(f"Pass 153K runtime diagnostics missing frame timing: {missing_diagnostics}")
print("Pass 153K OK: runtime separates update, draw, submitted-frame, and smoothed CPU timing")
