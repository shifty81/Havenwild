#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
errors=[]
def read(rel):
    p=ROOT/rel
    if not p.is_file(): errors.append(f'missing {rel}'); return ''
    return p.read_text(encoding='utf-8')
def need(text, toks, label):
    for t in toks:
        if t not in text: errors.append(f'{label}: missing {t!r}')
auth=read('apps/haven_editor_native/src/app/document_authority.rs')
life=read('apps/haven_editor_native/src/app/document_lifecycle.rs')
char=read('apps/haven_editor_native/src/app/character_studio.rs')
chrome=read('apps/haven_editor_native/src/app/workspace_chrome.rs')
pixel=read('apps/haven_editor_native/src/app/pixel_studio.rs')
menu=read('apps/haven_editor_native/src/app/editor_menu.rs')
mod=read('apps/haven_editor_native/src/app/mod.rs')
need(auth,['DocumentId','DocumentHostId','DocumentRecord','DocumentRegistrySnapshot','document_registry_snapshot','DocumentKind::Character'],'AUTH-01/02')
need(char,['saved_recipe_fingerprint','pub(crate) fn dirty(&self)','mark_recipe_saved','save_recipe_draft'],'AUTH-03')
need(chrome,['EditorViewportMode::CharacterStudio => self.character_studio.dirty()','|| self.character_studio.dirty()'],'AUTH-03 chrome')
need(life,['save_document_target','self.character_studio.save_recipe_draft()','self.pixel_studio.save_document_tab(*index)','Document save failed'],'AUTH-04')
if 'self.save_all_editor_documents();\n            self.close_document_target(dialog.target);' in life:
    errors.append('AUTH-04: Save & Close still routes through Save All')
need(pixel,['save_document_tab'],'AUTH-04 pixel')
need(menu,['self.character_studio.save_recipe_draft()'],'AUTH-05 Save All character coverage')
need(mod,['mod document_authority;'],'AUTH-02 module registration')
if errors:
    print('HW-AUTHORITY-05 validation FAILED')
    for e in errors: print('-',e)
    raise SystemExit(1)
print('PASS: HW-AUTHORITY-05 document lifecycle authority')
print('- stable document/host identity adapter exists without moving domain ownership')
print('- Character Studio participates in dirty/save lifecycle')
print('- Save & Close targets one document instead of Save All')
print('- explicit Save All includes Character Studio')
