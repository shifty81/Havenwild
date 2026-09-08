#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[5]
errors=[]
def read(rel):
 p=ROOT/rel
 if not p.is_file(): errors.append(f"missing {rel}"); return ""
 return p.read_text(encoding="utf-8")
editor=read("apps/haven_editor_native/src/app/collision_authoring.rs")
for m in ["prepare_scene_collision_reference","is_cell_walkable","wall_blocks_world_tile","furnishing_blocks_world_tile","update_collision_override_registry","collision_overrides_v1.json"]:
 if m not in editor: errors.append(f"editor collision authority missing: {m}")
bridge=read("apps/haven_editor_native/src/app/world_asset_pixel_bridge.rs")
for m in ['"Physical Collision Reference"','"Collision Add"','"Collision Subtract"','collision.add.png','collision.subtract.png','update_collision_override_registry']:
 if m not in bridge: errors.append(f"Pixel bridge collision round trip missing: {m}")
runtime=read("crates/haven_game/src/runtime_collision_overrides.rs")
for m in ["RuntimeCollisionOverrideRegistry","allows_position","add_mask","subtract_mask","mask_hit"]:
 if m not in runtime: errors.append(f"runtime collision overrides missing: {m}")
nav=read("crates/haven_game/src/runtime_scene_navigation.rs")
if "collision_override_registry.allows_position" not in nav: errors.append("runtime movement does not consume collision overrides")
cargo=read("crates/haven_game/Cargo.toml")
if "image.workspace = true" not in cargo: errors.append("haven_game must depend on image for authored collision masks")
registry=ROOT/"content/world/collision_overrides_v1.json"
if not registry.is_file(): errors.append("missing collision override registry")
else:
 data=json.loads(registry.read_text(encoding="utf-8"))
 if data.get("schema")!="havenwild.collision_override_registry.v1": errors.append("collision registry schema mismatch")
contract=ROOT/"content/editor/collision_authoring_w60e2_v1.json"
if not contract.is_file(): errors.append("missing W60E2 collision authoring contract")
else:
 data=json.loads(contract.read_text(encoding="utf-8"))
 if data.get("schema")!="havenwild.collision_authoring.w60e2.v1": errors.append("W60E2 contract schema mismatch")
 if data.get("runtime",{}).get("visualAlphaTracingIsAuthority") is not False: errors.append("sprite alpha must not become collision authority")
if errors:
 print("FAIL: W60E2 collision truth")
 for e in errors: print(" -",e)
 sys.exit(1)
print("PASS: W60E2 collision truth")
