#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]

def req(ok, msg):
    if not ok:
        raise AssertionError(msg)

def txt(rel):
    return (ROOT / rel).read_text(encoding='utf-8')

def main():
    authority = json.loads(txt('content/architecture/cliff_compile_hotfix_v0_1.json'))
    req(authority.get('pass') == '167Z109W8.1', 'compile hotfix authority pass mismatch')
    req(authority.get('behaviorPreserving') is True, 'compile hotfix must remain behavior-preserving')
    req(authority.get('terrainBehaviorChanges') is False, 'compile hotfix must not change terrain behavior')

    draw = txt('crates/haven_game/src/runtime_structural_cliff_draw.rs')
    req('pub(super) fn draw_cliff_source_cell(' in draw, 'shared cliff source-cell helper is not sibling-module visible')

    shapes = txt('crates/haven_game/src/runtime_structural_cliff_shapes.rs')
    start = shapes.index('pub(super) const fn authored_body_rows')
    end = shapes.index('/// Resolve the visual module count for one specific exposed structural edge.', start)
    helper_block = shapes[start:end]
    req('.max(' not in helper_block, 'const modular-height helper still uses Ord::max')
    req('usize::from(' not in helper_block, 'const modular-height helper still uses From::from')
    req('.saturating_sub(' not in helper_block, 'const modular-height helper still relies on a nonessential const library method')
    req('face_segments as usize' in helper_block, 'const modular-height helper is missing primitive cast')
    req('if face_segments == 0' in helper_block, 'const modular-height helper is missing zero-segment guard')

    caps = txt('crates/haven_game/src/runtime_structural_cliff_caps.rs')
    req('this.draw_cliff_source_cell(' in caps, 'cap renderer no longer reuses canonical source-cell helper')

    diag = txt('crates/haven_game/src/runtime_diagnostics.rs')
    req(('Pass 167Z109W8.1' in diag) or (('Pass 167Z109W9' in diag) or ('Pass 167Z109W10' in diag)), 'runtime diagnostics predates W8.1')
    req(any(x in txt('README.md') for x in ['Pass167Z109W8.1','Pass167Z109W9','Pass167Z109W10']), 'README predates W8.1')
    req(any(x in txt('docs/current/CURRENT_SOURCE_HANDOFF.md') for x in ['Pass167Z109W8.1','Pass167Z109W9','Pass167Z109W10']), 'handoff predates W8.1')
    print('Pass167Z109W8.1 cliff compile hotfix validated')

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'Pass167Z109W8.1 validation FAILED: {e}')
        raise
