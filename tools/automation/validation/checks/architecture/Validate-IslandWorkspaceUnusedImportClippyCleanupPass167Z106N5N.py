#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]

def fail(message: str) -> None:
    raise SystemExit(f"N5N island workspace strict-Clippy cleanup validation FAILED: {message}")

def main() -> None:
    path = ROOT / "apps/haven_editor_native/src/app/island_workspace.rs"
    if not path.is_file():
        fail("missing island_workspace.rs")
    text = path.read_text(encoding="utf-8")
    header = "\n".join(text.splitlines()[:12])
    if "draw_scissored_text" in header:
        fail("stale draw_scissored_text import remains in island_workspace.rs")
    if "draw_list_row" not in header:
        fail("shared list-row renderer import is missing")
    n5_validator = (ROOT / "tools/automation/validation/checks/architecture/Validate-RepositoryContentNormalizationPass167Z106N5.py").read_text(encoding="utf-8")
    if "explicit patch helper no longer cleans its transport removal manifest" in n5_validator:
        fail("N5 repository validator still expects the retired root patch-helper transport")
    if "patch packager no longer emits its transport removal manifest" not in n5_validator:
        fail("N5 repository validator does not enforce the current removal-manifest transport")
    print("N5N island workspace strict-Clippy cleanup validated")

if __name__ == "__main__":
    main()
