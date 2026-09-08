from pathlib import Path
ROOT = Path(__file__).resolve().parents[5]
g=(ROOT/'tools/automation/characters/Build-LpcPlayerAtlas.py').read_text()
p=(ROOT/'crates/haven_game/src/client_character_frontend_draw.rs').read_text()
r=(ROOT/'crates/haven_game/src/character_runtime_compositor.rs').read_text()
checks={
 'tintable eye mask':'make_tint_mask' in g and 'group_id == "eyes"' in g,
 'real feminine pair':'no feminine LPC body/head' in g,
 'unique hair assignment':'used_hair' in g and 'all_hair' in g,
 'eye tint reaches preview':'layer_color(appearance, "face/eyes"' in p,
 'feet draw after legs':p.find('layers.legs(appearance)') < p.find('layers.feet(appearance)'),
 'grounded shadow':'foot.y + 1.0' in r and 'foot.y - 64.0' in r,
}
missing=[k for k,v in checks.items() if not v]
if missing:
 print('Pass 149J24 FAILED'); [print('-',m) for m in missing]; raise SystemExit(1)
print('Pass 149J24 character visual fidelity and grounding validated')
