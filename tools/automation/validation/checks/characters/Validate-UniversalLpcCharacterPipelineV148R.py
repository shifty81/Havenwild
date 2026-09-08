#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT = Path(__file__).resolve().parents[5]
errors=[]
def require(path, token, label):
    text=(ROOT/path).read_text(encoding="utf-8")
    if token not in text: errors.append(f"{label}: missing {token!r} in {path}")
def check(cond,msg):
    if not cond: errors.append(msg)
profile=json.loads((ROOT/"content/characters/character_profile_world_policy_v1.json").read_text())
catalog=json.loads((ROOT/"content/characters/lpc_character_layer_catalog_v1.json").read_text())
pack=json.loads((ROOT/"content/asset_packs/havenwild_characters/pack.json").read_text())
check(profile.get("max_persistent_characters")==5,"persistent character limit must be 5")
check(profile.get("world_save_limit")=="unlimited","world save limit must be unlimited")
check(profile["menu_flow"]["new_game"][0]=="choose_character","new game must choose character first")
check(profile["menu_flow"]["load_game"][0]=="choose_character","load game must choose character first")
check(catalog.get("frame_cell")==[64,96],"LPC frame cell must be 64x96")
check(len(catalog.get("directions",[]))==8,"LPC profile must define eight directions")
slots={item["id"] for item in catalog.get("slots",[])}
for slot in ["body/base","hair/back","hair/front","clothing/torso","armor/torso","weapon/front"]: check(slot in slots,f"missing character slot {slot}")
consumers=set(catalog.get("consumers",[]))
for consumer in ["player_runtime","npc_runtime","character_creator","portrait_generator","multiplayer_replication"]: check(consumer in consumers,f"missing consumer {consumer}")
semantics={asset["semantic_id"] for asset in pack.get("assets",[])}
for semantic in ["character.layers.lpc.standard","character.profile.policy","character.npc.generated","character.player.layered"]: check(semantic in semantics,f"missing semantic provider {semantic}")
require("crates/haven_save/src/character_profiles.rs","MAX_PERSISTENT_CHARACTERS: usize = 5","five-character store")
require("crates/haven_save/src/character_profiles.rs","scan_unlimited_world_saves","unlimited world scan")
require("crates/haven_save/src/character_profiles.rs","CharacterWorldLink","world-local character link")
require("crates/haven_assets/src/lpc_character_pipeline.rs","CharacterLayerIndex","layer index")
require("crates/haven_game/src/character_frontend_flow.rs","ChooseCharacter","character-first frontend flow")
require("crates/haven_game/src/character_frontend_flow.rs","ChooseWorld","world selection after character")
if errors:
    print("Pass 148R FAILED")
    for error in errors: print(" -",error)
    sys.exit(1)
print("Pass 148R universal LPC character pipeline validated")
print(f"slots={len(slots)} animations={len(catalog.get('animation_families',[]))} consumers={len(consumers)}")
