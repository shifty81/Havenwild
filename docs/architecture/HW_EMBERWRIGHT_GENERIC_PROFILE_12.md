# HW-EMBERWRIGHT-GENERIC-PROFILE-12

Baseline: `HW-PCC-PATCH-INTAKE-HARDENING-11R1` or newer.

## Purpose

Start the safe generic-editor migration without renaming crates or removing
existing Havenwild functionality.

The product direction is:

- **Ember**: broader runtime/engine/package ecosystem.
- **Emberwright**: focused native 2D game-maker/editor application.
- **Havenwild**: first real hosted game project/profile inside Emberwright.

## Important rule

Phase 3 does **not** mean hand-moving values into a permanent Havenwild-only
object. The generic editor must be able to recreate equivalent profile values
through a straightforward workflow:

1. Create/import project.
2. Choose 2D template.
3. Configure canvas/tile/layer model.
4. Import source libraries.
5. Classify source sheets.
6. Promote semantic assets.
7. Define project vocabulary.
8. Configure runtime launch/PIE.
9. Validate profile.
10. Publish profile.

## Files added

- `content/editor/product/emberwright_identity_v0_1.json`
- `content/editor/project_profile/project_profile_schema_v0_1.json`
- `content/editor/project_profile/havenwild_project_profile_seed_v0_1.json`
- `content/editor/project_profile/profile_creation_workflow_v0_1.json`
- `content/editor/project_profile/havenwild_specific_value_migration_inventory_v0_1.json`
- `tools/automation/project/Write-EmberwrightProjectProfileAudit.py`

## Why this is intentionally additive

The editor already has real systems: Game Canvas, Assets, Pixel, Animation,
Character, Logic, Sound, command registry, workspace shell, docks, asset palette,
published asset/topology registries, and Play/Play From Here. This pass preserves
those systems and adds the generic profile authority beside them.

## Next implementation pass

After the Assets input recovery is verified, the next code pass should wire a
small `ProjectProfile` loader into editor startup and expose profile data in the
About/status or diagnostics panel while keeping all current hard-coded fallbacks.
