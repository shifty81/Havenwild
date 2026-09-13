# Havenwild Forge GUI Editor Normalization Audit — Pass 22

## Direction

The Atlas Mapper Lite tool is the small certification surface for source tile sheets. The same Forge GUI direction should now be migrated across the main Havenwild editor and the future Emberwright/GameMaker-style infinite canvas editor shell.

## Immediate GUI standard

Every editor surface should converge on:

- dark themed panel surfaces
- clear header bands
- status pills for live state
- readable hover/active/focus states
- scrollable panels with dark scrollbars
- stable left resource tree
- permanent center canvas/document area
- right inspector/properties lane
- bottom output/problems/activity/chat lane
- opaque overlay rails for tools and layers
- no modal islands for normal authoring tools

## Mapper-specific normalization

Atlas Mapper Lite should plug into the asset-intake lane rather than being a detached experiment.

Desired asset lane flow:

```text
Asset Authority / Tile Sheets
  -> LPC Terrain
  -> LPC Objects
  -> LPC Structure
  -> LPC Characters
  -> LPC FX
  -> External Roots
      sheet row [green mapped indicator if mapped-sheet record exists]
      open selected sheet in Atlas Mapper Lite
      save mapper project
      export handoff
      promote to Asset Authority candidate
```

## Main editor migration targets

1. Asset Studio becomes Asset Authority panels, not a trapping center workspace.
2. Pixel/Animation/Character/Logic/Sound become document tools and dockable panels.
3. Room/Game Canvas remains the permanent center.
4. Forge GUI components become the common renderer contract for the editor.
5. Atlas Mapper output feeds PublishedWorldAssetMetadata candidates through governed import, not loose JSON guessing.

## Pass 22 boundary

This pass updates the mapper GUI, mapped-state evidence, auto mapping, and PCC menu placement. It does not yet import handoffs into runtime published assets.
