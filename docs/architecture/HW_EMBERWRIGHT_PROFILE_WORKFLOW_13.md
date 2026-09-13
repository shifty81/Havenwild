# HW-EMBERWRIGHT-PROFILE-WORKFLOW-13

Baseline target: `HW-EMBERWRIGHT-GENERIC-PROFILE-12` / `d2a58481b32578b6c4610ea7af3c675fd342a947`

Behavior change: **none**. This pass is a safe generic-editor workflow authority pass.

## Purpose

The editor is moving toward **Emberwright**: a generic native 2D game-maker/editor. Havenwild remains the first hosted project and must keep working, but its project-specific values should not become permanent editor-shell assumptions.

This pass locks the answer to the Phase 3 concern:

> When Havenwild-specific values move into `HavenwildProjectProfile`, the generic side must be able to recreate an equivalent profile through a straightforward workflow.

## Added authorities

- `content/editor/project_profile/generic_profile_creation_contract_v0_1.json`
- `content/editor/project_profile/profile_wizard_steps_v0_1.json`
- `content/editor/project_profile/havenwild_profile_recreation_recipe_v0_1.json`
- `content/editor/architecture/emberwright_genericization_pass_matrix_v0_1.json`
- `tools/automation/project/Write-EmberwrightProfileWorkflowReport.py`

## Workflow now expected from the generic side

```text
Create/import project
→ choose 2D template
→ configure canvas/tile/layer model
→ import source libraries
→ classify source sheets
→ promote semantic assets
→ define project vocabulary
→ configure runtime / PIE
→ validate profile
→ publish profile
```

## Why this preserves current functionality

This pass does not rename crates, change runtime launch, change validation profiles, change editor tabs, or move any Havenwild constants yet. It adds the generic workflow contract first so the later migration can be deliberate and testable.

## Next implementation pass

`HW-EMBERWRIGHT-PROFILE-SEAM-14` should add code-level `ProjectProfile` query helpers beside current hardcoded values. The first code seam should be read-only and conservative: it should report the active editor identity, default workspaces, tile size, runtime profile, and profile migration inventory without changing existing behavior.
