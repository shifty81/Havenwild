# Ember Handoff: Havenwild Asset Mapping Workspace

Havenwild's Atlas Mapper should be treated as the first vertical slice of Ember's future Asset Mapping Workspace.

## Ingest target

Ember should ingest the concept as a generic profile-driven workspace:

- Asset Library panel
- Source Tile Sheet panel
- Scene Draft canvas
- Layer Stack panel
- Semantic Inspector
- Socket/Edge editor
- Pixel Collision editor
- Variant/Randomization tools
- Animation Strip mapper
- Preview/Validation panel
- Publish Candidate panel

Havenwild then becomes the hosted project profile that supplies its asset families, semantic rules, terrain/cliff rules, layer model, collision requirements, and runtime publication contracts.

## Branch model

Main remains the stable GREEN Havenwild lane. Heavy editor/tooling work should move to `experiment/asset-mapper-workspace` until the mapper, asset lane, PCC branch workflow, and Forge GUI portability are proven.

## Merge requirement

Do not merge to main until the experimental branch can run the internal PCC Full Quality Gate and the mapper can prove source-mapped sheets, handoff export, and mapped-sheet status without breaking runtime/editor launch.
