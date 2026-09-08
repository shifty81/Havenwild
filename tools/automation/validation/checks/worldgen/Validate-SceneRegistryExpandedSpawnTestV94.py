#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
SOURCE = ROOT / "crates/haven_core/src/scene_registry.rs"


def main() -> int:
    text = SOURCE.read_text(encoding="utf-8")
    required = [
        "let cellar = SceneMap::starter(SceneId::Cellar, SceneKind::Cave, 2, 2);",
        "let expected_cellar_spawn_x = cellar.spawn_x;",
        "let registry = SceneRegistry::from(vec![farmstead, cellar]);",
        "expected_cellar_spawn_x",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        for item in missing:
            print(f"missing scene-registry migration-safe test contract: {item}")
        return 1

    stale = '''.spawn_x,\n            2\n        );'''
    if stale in text:
        print("scene registry test still hard-codes the pre-expansion cellar spawn x")
        return 1

    print("Scene registry expanded-spawn test contract passed (V94)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
