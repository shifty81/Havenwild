#!/usr/bin/env python3
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[5]
def require(path: str, needles: list[str]) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"V139 missing {needle!r} in {path}")

require("crates/haven_world/src/world_topology.rs", [
    'WORLD_TOPOLOGY_SCHEMA',
    'HorizontalWrapMode::EastWest',
    'tile.x.rem_euclid(self.width_tiles)',
    'shortest_wrapped_delta_x',
    'nearest_unwrapped_x',
    'WorldChunkPersistenceKey',
    'seam_neighbors_are_contiguous',
])
require("crates/haven_world/src/open_world.rs", [
    'wrap_east_west: true',
    'clamp_north_south: true',
    'pub fn topology(&self)',
    'pub fn canonical_tile(&self',
])
require("crates/haven_world/src/lib.rs", ['pub mod world_topology;', 'pub use world_topology::*;'])
require("crates/haven_save/src/lib.rs", [
    'world_wrap_east_west',
    'world_topology.json',
    'save_world_topology_to_path',
    'load_world_topology_from_path',
])
save_text = (ROOT / 'crates/haven_save/src/lib.rs').read_text(encoding='utf-8')
match = re.search(r'CURRENT_CLIENT_GENERATION_VERSION: u32 = (\d+)', save_text)
if not match or int(match.group(1)) < 4:
    raise SystemExit('V139 requires client generation version 4 or newer')
if int(match.group(1)) > 4:
    contract = json.loads((ROOT / 'content/worldgen/chunk_persistence_contract_v1.json').read_text(encoding='utf-8'))
    migration = contract.get('migrationPolicy', {})
    if migration.get('currentClientGenerationVersion') != int(match.group(1)) or 4 not in migration.get('supportedFromVersions', []):
        raise SystemExit('V139 current save generation advanced without a declared migration from version 4')
require("content/validation/validation_manifest_v1.json", ['Validate-WrappedWorldCoordinateFoundationV139.py'])
print(f"Pass 139 wrapped-world coordinate foundation validated against client generation v{match.group(1)}")
