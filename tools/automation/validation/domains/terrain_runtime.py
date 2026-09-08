from __future__ import annotations
from pathlib import Path

from validation.domains.current_contract import run_current_contract
from validation.validate_content_integrity import validate_direct_lpc_terrain_authority


def validate(entry, root: Path):
    return run_current_contract(entry, [
        ("direct LPC terrain source and exact-pair runtime authority", validate_direct_lpc_terrain_authority),
    ])
