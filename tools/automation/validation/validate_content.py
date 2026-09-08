#!/usr/bin/env python3
"""Compatibility wrapper for the canonical Havenwild project-content validator."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/automation"))

from validation.validate_project_content import (  # noqa: E402
    VALIDATOR_REVISION,
    main,
    run_self_test,
    should_skip,
    validate_tree,
)

__all__ = [
    "VALIDATOR_REVISION",
    "main",
    "run_self_test",
    "should_skip",
    "validate_tree",
]


if __name__ == "__main__":
    raise SystemExit(main())
