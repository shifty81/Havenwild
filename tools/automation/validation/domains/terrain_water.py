from __future__ import annotations
from pathlib import Path

from validation.domains.current_contract import run_current_contract
from validation.validate_content_integrity import (
    validate_client_test_world_materialization,
    validate_terrain_topology_certification,
)


def validate(entry, root: Path):
    return run_current_contract(entry, [
        ("client open-world biome, coast, pond, and water-depth materialization", validate_client_test_world_materialization),
        ("terrain topology and LPC water-edge evidence", validate_terrain_topology_certification),
    ])
