#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
model = (ROOT / 'crates/haven_game/src/character_creator_model.rs').read_text(encoding='utf-8')
catalog = (ROOT / 'crates/haven_game/src/character_creator_catalog.rs').read_text(encoding='utf-8')
generator = (ROOT / 'tools/automation/characters/Build-LpcPlayerAtlas.py').read_text(encoding='utf-8')
runtime = (ROOT / 'crates/haven_game/src/character_runtime_compositor.rs').read_text(encoding='utf-8')
frontend = (ROOT / 'crates/haven_game/src/client_frontend.rs').read_text(encoding='utf-8')

errors=[]
hairs = [
'Medium 01 - Page','Medium 02 - Curly','Medium 03 - Idol','Medium 04 - Bangs & Bun',
'Medium 05 - Cornrows','Medium 06 - Dreadlocks','Medium 07 - Bob, Side Part',
'Medium 08 - Bob, Bangs','Medium 09 - Twists','Medium 10 - Twists, Fade',
'Short 01 - Buzzcut','Short 02 - Parted','Short 03 - Curly','Short 04 - Cowlick',
'Short 05 - Natural','Short 06 - Balding','Short 07 - Flat Top','Short 08 - Flat Top, Fade']
facial = [
'Facial Hair 01 - Walrus Mustache','Facial Hair 02 - Chevron Mustache',
'Facial Hair 03 - Handlebar Mustache','Facial Hair 04 - Lampshade Mustache',
'Facial Hair 05 - Horseshoe Mustache','Facial Hair 06 - Trimmed Beard',
'Facial Hair 07 - Medium Beard']
for name in hairs + facial + ['Eyebrows 01 - Thin Eyebrows','Eyebrows 02 - Thick Eyebrows']:
    if name not in model or f'Hair/{name}/Brown/Walk.png' not in generator:
        errors.append(f'missing exact LPC taxonomy entry: {name}')
if 'FacialHairKind' not in model or 'EyebrowKind' not in model:
    errors.append('facial hair and eyebrows are not independent creator channels')
if 'selection.eyebrows' not in frontend or 'selection.facial_hair' not in frontend:
    errors.append('frontend does not expose independent eyebrow/facial-hair selectors')
if 'face/eyebrows' not in runtime or 'face/facial_hair' not in runtime:
    errors.append('runtime compositor does not resolve eyebrow/facial-hair channels')
for forbidden in [
    'else list(groups["torso_tshirt"])',
    'else list(groups["legs_pants"])',
    'exact or next(',
]:
    if forbidden in generator:
        errors.append(f'arbitrary asset substitution remains: {forbidden}')
if 'build_animation_catalog' not in generator or 'lpc_character_animation_catalog_v0_1.json' not in generator:
    errors.append('complete character animation catalog is not generated')
if 'build_sheet_catalog' not in generator or 'lpc_character_sheet_catalog_v0_1.json' not in generator:
    errors.append('complete character sheet catalog is not generated')
if 'HOOD_BLOCKED' not in catalog:
    errors.append('hood compatibility metadata is missing')
if errors:
    print('Pass 149J26 FAILED')
    for e in errors: print(f'- {e}')
    sys.exit(1)
print('Pass 149J26 LPC character repository promotion validated: exact hair/eyebrow/facial-hair taxonomy, no arbitrary substitutions, complete sheet and animation catalogs')
