#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
MIGRATION = ROOT / "crates/haven_core/src/foundation/scene_size_migration.rs"
FOUNDATION = ROOT / "crates/haven_core/src/foundation.rs"


def main() -> int:
    issues: list[str] = []
    migration = MIGRATION.read_text(encoding="utf-8")
    foundation = FOUNDATION.read_text(encoding="utf-8")

    if "use crate::ProjectSceneId;" not in migration:
        issues.append("scene_size_migration.rs must import ProjectSceneId from the crate root")
    if "starter_biome, ProjectSceneId" in migration or "ProjectSceneId, SceneBiome" in migration:
        issues.append("scene_size_migration.rs still imports ProjectSceneId through foundation::super")
    if "use scene_size_migration::legacy_scene_offset;" in foundation:
        issues.append("foundation.rs retains the unused legacy_scene_offset import")
    if "pub(crate) const fn legacy_scene_offset()" not in migration:
        issues.append("legacy_scene_offset helper was removed instead of remaining module-local")
    for token in [
        "default_biome_for_project_scene",
        "center_legacy_zone_grid",
        "migrate_legacy_transition",
        "scene_dimension_offset",
    ]:
        if token not in migration:
            issues.append(f"migration helper missing after hotfix: {token}")

    if issues:
        print("Expanded scene scale compile hotfix validation FAILED")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("Expanded scene scale compile hotfix validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
