# Pass109 LPC Closed Sand/Grass Corner Hotfix

Superseded by Pass110. The global closed-corner mask shortcut in this pass
regressed wet-sand and shoreline families and must not be restored.

Pass109 fixes the remaining square owner-color chunks visible when painting sand
over grass in compound shapes.

The previous resolver handled simple edges, simple adjacent corners, and pure
diagonal inner corners. It did not use the already-detected `outer_corners`
topology when adjacent sand edges were closed by sand on the diagonal. Those
closed corner cells kept the authored grass-corner role, leaving square green
blocks inside sand paths and small painted regions.

## Runtime Contract

- Open adjacent edge corners still use the authored LPC corner role.
- Single edge plus diagonal remains a single outer replacement role.
- Closed adjacent sand/grass corners resolve to the baked compound-fill mask.
- Compound fill uses the verified repeatable neighbor fill and does not expose
  the owner base tile.

## Validation

- `tools/automation/validation/checks/terrain/Validate-LpcClosedSandGrassCornerTopologyV121.py`
- wired into `tools/build/Build.sh all` before Cargo
- wired into `tools/automation/validation/validate.py`
