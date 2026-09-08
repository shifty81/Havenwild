from __future__ import annotations
from pathlib import Path

from validation.domains.current_contract import run_current_contract
from validation.validate_content_integrity import (
    validate_lpc_production_assets,
    validate_terrain_topology_certification,
)


def validate(entry, root: Path):
    return run_current_contract(entry, [
        ("production LPC terrain and livestock registry", validate_lpc_production_assets),
        ("promoted terrain acceptance coverage", validate_terrain_topology_certification),
    ])
