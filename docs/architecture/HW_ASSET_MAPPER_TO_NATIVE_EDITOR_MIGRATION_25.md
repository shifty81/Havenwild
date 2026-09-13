# Atlas Mapper to Native Editor Migration

## Decision

The Atlas Mapper Lite remains useful as a standalone prototype, but the target implementation is a dockable Asset World Mapping Workspace inside the Havenwild native editor.

## Migration phases

1. Keep standalone mapper gate-green while adding mapping records and correction-scene semantics.
2. Add the same source sheet stack and mapping status model to the native editor Asset workspace.
3. Replace the mapper's blank assembly canvas with a native editor world canvas adapter.
4. Add real layer rail and tool rail controls for tile replacement, collision, sockets, and semantic roles.
5. Move shared GUI chrome to ForgeGuiCore/EmberGuiCore instead of duplicating debug-style panels.
6. Export an Ember ingest handoff so Ember can absorb the generic editor modules while Havenwild becomes a hosted project profile.

## Non-goals

- Do not mutate source PNG atlases.
- Do not auto-publish mapped cells into runtime without validation.
- Do not treat the standalone mapper as the permanent production editor shell.
- Do not create another one-off UI toolkit.

## Required data loop

```text
Source Sheet Stack
  -> World Canvas Draft/Generated Map
  -> User Tile/Layers/Collision/Sockets Corrections
  -> Learn From Scene
  -> Mapping/Coverage Records
  -> Handoff Evidence
  -> Asset Authority Validation
  -> Runtime Publication
```
