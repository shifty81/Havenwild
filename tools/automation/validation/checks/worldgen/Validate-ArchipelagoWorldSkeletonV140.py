from pathlib import Path
import json
ROOT = Path(__file__).resolve().parents[5]
def req(p, needles):
 t=(ROOT/p).read_text(encoding='utf-8')
 for n in needles:
  assert n in t, f"{p} missing {n}"
config=json.loads((ROOT/'content/worldgen/archipelago_world_skeleton_v1.json').read_text())
assert config['schema']=='havenwild.archipelago_skeleton.v1'
assert config['requirements']['mainland_count']==1
assert config['requirements']['minimum_major_island_count']>=10
assert len(set(config['major_biomes']))>=10
assert config['shore_band_tiles'] < config['shallow_band_tiles'] < config['shelf_band_tiles']
req('crates/haven_world/src/archipelago_skeleton.rs',['ArchipelagoSkeleton','LandmassClass::Mainland','MajorIsland','MinorIsland','OceanDepthBand','authored_anchors','at least ten major islands'])
req('crates/haven_world/src/lib.rs',['pub mod archipelago_skeleton;','pub use archipelago_skeleton::*;'])
req('content/validation/validation_manifest_v1.json',['Validate-ArchipelagoWorldSkeletonV140.py'])
print('Pass 140 archipelago world skeleton validated')
