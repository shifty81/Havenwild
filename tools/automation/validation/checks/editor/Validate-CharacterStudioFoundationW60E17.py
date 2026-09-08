#!/usr/bin/env python3
from pathlib import Path
import json,sys
R=Path(__file__).resolve().parents[5]; errors=[]
cs=(R/'apps/haven_editor_native/src/app/character_studio.rs').read_text(encoding='utf-8'); layers=(R/'apps/haven_editor_native/src/app/canvas_layers.rs').read_text(encoding='utf-8')
for m in ['CharacterRecipeDraft','Remove','Character Wardrobe','Assembled Character Preview']:
 if m not in cs: errors.append('character studio current authority missing '+m)
legacy=['Assign','Save Preset','Load Preset']
creator=['Character Creator','Add Selected','PRESET','Restart Animation']
if not all(m in cs for m in legacy) and not all(m in cs for m in creator): errors.append('character studio lacks either legacy W60E17 controls or W81R5 production creator controls')
# R31 replaces the old one-row 'Character Parts' shell with recipe-derived semantic
# Character Layers while preserving the same CharacterParts layer kind and advanced
# attachment/source diagnostics. Validate the modern authority instead of reviving
# a duplicate generic row.
for m in ['CanvasLayerKind::CharacterParts','Attachment / Sockets','Source / zPos Diagnostics']:
 if m not in layers: errors.append('character shared shell layer missing '+m)
try:
 data=json.loads((R/'content/editor/ui/character_studio_foundation_w60e17_v1.json').read_text(encoding='utf-8'))
 if data.get('schema') is None: errors.append('E17 contract schema missing')
except Exception as e: errors.append('E17 contract invalid: '+str(e))
# W76 supersedes the old E17 "static-only" UX; verify the newer capability rather than rejecting it.
if 'Advanced' not in cs or not ('Randomize Unlocked' in cs or 'All Unlocked' in cs): errors.append('W76/W81R5 Character Studio supersession markers missing')
if errors:
 print('FAIL: W60E17 Character Studio foundation'); [print(' -',e) for e in errors]; sys.exit(1)
print('PASS: W60E17 Character Studio foundation (superseded by W76 wardrobe workflow)')
