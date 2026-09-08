#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
errors=[]

def read(rel):
    p=ROOT/rel
    if not p.is_file():
        errors.append(f"missing {rel}")
        return ""
    return p.read_text(encoding='utf-8')

text=read('apps/haven_editor_native/src/app/editor_text.rs')
mod=read('apps/haven_editor_native/src/app/mod.rs')

w72b_contract = ROOT / 'content/editor/text/editor_font_atlas_w72b_v2.json'
if w72b_contract.is_file():
    # W72B supersedes W60A's built-in-font experiment with a persistent Segoe
    # atlas plus explicit mutation barriers. Preserve W60A's single-authority
    # invariant without requiring the retired experimental markers.
    for marker in [
        'Dedicated Segoe UI editor font atlas.',
        'flush_editor_batches_before_font_atlas_mutation',
        'ensure_editor_font_glyphs',
        'gl_use_default_material();',
        'draw_text_ex(',
        'pub(crate) fn editor_font_ready() -> bool',
    ]:
        if marker not in text:
            errors.append(f'W72B editor_text.rs missing marker: {marker}')
else:
    for marker in [
        'Stable built-in editor font authority active',
        'HAVENWILD_EDITOR_EXPERIMENTAL_SYSTEM_FONT',
        'gl_use_default_material();',
        'draw_text(text, x, y, font_size, color)',
        'pub(crate) fn editor_font_ready() -> bool',
    ]:
        if marker not in text:
            errors.append(f'editor_text.rs missing marker: {marker}')

if mod.count('initialize_editor_font()') != 1:
    errors.append('editor bootstrap must initialize font authority exactly once')
if 'initialize_editor_font()' in read('apps/haven_editor_native/src/app/editor_menu.rs'):
    errors.append('menu/client lifecycle must not rebuild font authority')

if errors:
    print('FAIL: W60A editor text authority')
    for e in errors: print(' -',e)
    sys.exit(1)
print('PASS: W60A editor text authority')
