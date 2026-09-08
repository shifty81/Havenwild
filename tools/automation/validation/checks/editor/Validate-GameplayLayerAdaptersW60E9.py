#!/usr/bin/env python3
from pathlib import Path
import sys
R=Path(__file__).resolve().parents[5]; errors=[]
def t(x):
 p=R/x
 if not p.is_file(): errors.append('missing '+x); return ''
 return p.read_text(encoding='utf-8')
core=t('crates/haven_core/src/foundation/scene_world.rs'); layers=t('apps/haven_editor_native/src/app/canvas_layers.rs'); auth=t('apps/haven_editor_native/src/app/gameplay_layer_authoring.rs')
for m in ['SceneSemanticLayer','semantic_cell','NavigationBlock','LogicBinding','!self.semantic_layers.has(x, y, SceneSemanticLayer::NavigationBlock)']:
 if m not in core: errors.append('missing E9 core '+m)
# H21 A9-A14 normalized visible world/scene layers into concise groups.
# W60E9 therefore validates the semantic capability kinds and their canonical
# authoring adapter mappings rather than requiring one visible row per bit-layer.
for marker in [
    'label: "Navigation".into()',
    'scene_layer_grouped("Gameplay"',
    '    Interaction,',
    '    WaterSwim,',
    '    SpawnPopulation,',
    '    BuildabilityFarming,',
    '    LogicBindings,',
]:
    if marker not in layers:
        errors.append('missing E9 grouped layer capability '+marker)
for marker in [
    'Some(L::Navigation) => Some(SceneSemanticLayer::NavigationBlock)',
    'Some(L::Interaction) => Some(SceneSemanticLayer::Interaction)',
    'Some(L::WaterSwim) => Some(SceneSemanticLayer::WaterSwim)',
    'Some(L::SpawnPopulation) => Some(SceneSemanticLayer::SpawnPopulation)',
    'Some(L::BuildabilityFarming) => Some(SceneSemanticLayer::BuildabilityFarming)',
    'Some(L::LogicBindings) => Some(SceneSemanticLayer::LogicBinding)',
]:
    if marker not in auth:
        errors.append('missing E9 semantic adapter mapping '+marker)
for m in ['apply_active_scene_semantic_tool','draw_active_scene_semantic_overlay']:
 if m not in auth: errors.append('missing E9 adapter '+m)
if 'pub fn starter_seeded' not in core or 'pub fn autotile_override_at' not in core:
 errors.append('missing SceneMap starter_seeded constructor boundary')
else:
 starter=core.split('pub fn starter_seeded',1)[1].split('pub fn autotile_override_at',1)[0]
 if 'semantic_layers: SceneSemanticLayers::default(),' not in starter:
  errors.append('SceneMap::starter_seeded must initialize semantic_layers')
if '.scenes.get_mut(' in auth:
 errors.append('SceneRegistry has no DerefMut; semantic authoring must use get_at_mut/by_id_mut')
if '.scenes.get_at_mut(self.selected_scene)' not in auth:
 errors.append('semantic authoring must mutate the selected SceneRegistry entry through get_at_mut')
if errors:
 print('FAIL: W60E9 gameplay layer adapters'); [print(' -',e) for e in errors]; sys.exit(1)
print('PASS: W60E9 gameplay layer adapters')
