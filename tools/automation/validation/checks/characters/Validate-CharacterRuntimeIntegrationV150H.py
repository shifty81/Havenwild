from pathlib import Path
ROOT = Path(__file__).resolve().parents[5]
errors=[]
def req(rel, token, label):
 p=ROOT/rel
 if not p.exists(): errors.append(f"missing {rel}"); return
 if token not in p.read_text(encoding='utf-8'): errors.append(f"{label}: missing {token!r} in {rel}")
main=ROOT/'crates/haven_game/src/main.rs'
text=main.read_text(encoding='utf-8')
for obsolete in ['client_character_creation','client_character_creator_ui','client_character_sprite_runtime']:
 if f'mod {obsolete};' in text or (ROOT/f'crates/haven_game/src/{obsolete}.rs').exists(): errors.append(f'obsolete Pass 140 lane remains: {obsolete}')
for mod in ['character_creator_model','character_runtime_compositor','client_character_frontend_draw','character_world_runtime','character_world_sync','client_entry']:
 if f'mod {mod};' not in text: errors.append(f'active module not registered: {mod}')
req('crates/haven_game/src/client_entry.rs','ClientFrontend::new().await','async frontend construction')
req('crates/haven_game/src/client_entry.rs','RuntimeAssets::load(&launch.character_id).await','character-aware runtime assets')
req('crates/haven_game/src/client_frontend.rs','scan_world_saves','dynamic world discovery')
req('crates/haven_game/src/client_frontend.rs','CharacterProfileStore','portable character profiles')
req('crates/haven_game/src/runtime_persistence.rs','persist_character_world_state','character-world persistence')
req('crates/haven_game/src/runtime_draw.rs','character_runtime','runtime character compositor use')
req('crates/haven_game/src/character_world_sync.rs','persist_character_world_state','character world sync save')
if errors:
 print('Pass 150H FAILED')
 for e in errors: print(' -',e)
 raise SystemExit(1)
print('Pass 150H OK: active character creator/runtime/persistence lane is constructed and obsolete Pass 140 modules are absent')
