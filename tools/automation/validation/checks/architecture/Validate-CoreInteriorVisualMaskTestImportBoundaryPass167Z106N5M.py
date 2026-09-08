#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]

def fail(message: str) -> None:
    raise SystemExit(f"N5M core interior visual-mask test import boundary validation FAILED: {message}")

def main() -> None:
    path = ROOT / "crates/haven_core/src/foundation/foundation_tests.rs"
    if not path.is_file():
        fail("missing foundation_tests.rs")
    text = path.read_text(encoding="utf-8")
    if "ProjectSceneId::new(\"mask_test_exterior\")" not in text:
        fail("expected exterior visual-mask regression test is missing")
    if "use crate::ProjectSceneId;" not in text:
        fail("foundation test module does not explicitly import crate::ProjectSceneId")
    if "use super::*;\nuse crate::ProjectSceneId;" not in text:
        fail("ProjectSceneId import is not kept at the test-module boundary")
    print("N5M core interior visual-mask test import boundary validated")

if __name__ == "__main__":
    main()
