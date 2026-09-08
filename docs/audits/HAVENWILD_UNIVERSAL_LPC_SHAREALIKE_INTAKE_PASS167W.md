# Havenwild Pass 167W — Universal LPC ShareAlike Intake

This pass makes all 2,038 verified CC-BY-SA Universal LPC credit records selectable through the mounted source authority. It does not duplicate the 138 MB source repository into the incremental patch.

## Runtime and editor policy

- Preferred CC0/OGA-BY/CC-BY components remain preferred when equivalent.
- CC-BY-SA components are selectable for players, NPCs, populations, and monsters.
- Every recipe records exact source dependencies and whether ShareAlike applies.
- Generated composites containing a ShareAlike layer are marked for the open-assets export lane.

## Release policy

A commercial build using conditional assets must export the exact used sources, modified overrides, affected generated composites, credits, source URLs, selected license, and modification notes. The exported open-assets directory must not be hidden behind effective technological restrictions.

Use `tools/automation/release/Build-UniversalLpcOpenAssetBundleV167W.py` with a usage manifest. `--include-all-conditional` is available for development or complete archival exports, but used-only output is the production default.
