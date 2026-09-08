from pathlib import Path
import sys
root = Path(__file__).resolve().parents[5]
lib = root / 'crates/haven_tools/src/lib.rs'
text = lib.read_text(encoding='utf-8')
if 'pub use haven_assets::*' in text or 'pub use haven_world::*' in text or 'pub use haven_editor::*' in text:
    print('haven_tools still uses broad glob re-exports')
    sys.exit(1)
for required in ['pub use haven_assets as assets;', 'pub use haven_editor as editor;', 'pub use haven_world as world;']:
    if required not in text:
        print(f'missing namespaced export: {required}')
        sys.exit(1)
print('haven_tools namespaced export validation passed.')
