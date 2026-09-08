from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[5]
TARGET = ROOT / "crates/haven_game/src/player_inventory_ui/station_processing.rs"

def fail(message: str) -> None:
    print(f"FAILED Pass167Z106N5B station-processing parse hotfix: {message}")
    raise SystemExit(1)

if not TARGET.is_file():
    fail(f"missing {TARGET.relative_to(ROOT)}")

text = TARGET.read_text(encoding="utf-8")
if re.search(r"#\[[^\]]+\]\s*\n\s*}", text):
    fail("dangling Rust attribute remains immediately before a closing brace")
if not text.rstrip().endswith("}"):
    fail("station-processing module does not end with a completed item/impl brace")
if "#[allow(dead_code)]\n}" in text:
    fail("orphaned dead_code attribute from the N4 decomposition remains")

print("Pass167Z106N5B station-processing parse hotfix validated")
