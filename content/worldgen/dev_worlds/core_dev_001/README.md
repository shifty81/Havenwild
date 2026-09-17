# Havenwild canonical Base World

This directory owns **the single authored development world** used by the native
editor and the external development client. Story and Sandbox will consume its
published content through separate gameplay/generation profiles; they must not
become competing editor worlds.

- `development_world.json`: project-owned identity, selected initial scene and
  development character. It must not be replaced with a machine-local descriptor.
- `world.tworld`: the authored source, materialized by the native editor **once**
  on first launch when missing. The editor reopens this exact file thereafter.
- `worldgen/world_creation_settings.json` and the semantic-world bake: sidecars
  persisted alongside the authored source by the editor.
- `WORKSPACE/saves/world_core_dev_001/world.tworld`: disposable replica for the external
  development client, not an editor authority or fallback world.

First launch starts from the existing scene-rectangle manifest and Havenwild
landmass generator. It deliberately discards the historical nine-scene starter
fixture from the new base's scene registry; the old fixture is still available
in code for explicit compatibility testing. First launch does **not** reroll or
rewrite the authored scene-rectangle manifest.

Saving validates the mainland and scene registry, writes the source, reads and
validates it again, then writes the client replica. Save & Push reloads the
same source in a running development client. Play From Here is an external
process until real editor-embedded PIE is implemented and certified.

If `world.tworld` exists but cannot load or lacks required generated scenes,
startup displays the error and disables Base World Save/Play rather than
silently replacing it with starter content. Normal client New World still
uses the shared materializer to create independent world instances; **applying
protected authored Base World overrides and Story/Sandbox rules to client New
World is a later, separately tested step**, not completed by this patch.

Do not store player/world-instance saves here. A normal Git commit must include
intentional changes to the authored world and associated sidecars.
