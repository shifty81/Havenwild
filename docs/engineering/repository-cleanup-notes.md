# Repository Cleanup Notes

## Purpose

Record what was removed during the repo cleanup so the current source layout stays intentional.

## Removed Categories

### Legacy runtime code

- removed the old root `src/` runtime tree
- removed the preserved `legacy/` platformer tree

Reason:

- neither tree belonged to the active Rust workspace
- both represented an older side-scroller direction that conflicted with the current tavern game/editor focus

### Old plugin / mod-kit source

- removed `SOFTWARE/plugins`
- removed `MODS`
- removed `SDK_FACTORY`

Reason:

- these folders belonged to an earlier Travellers Rest plugin/mod-kit direction
- they no longer matched the standalone Havenwild Prototype game + editor architecture

### Generated / local-only bloat

- removed `target`
- removed `logs`
- removed `docs/website/node_modules`
- removed `docs/website/dist`
- removed `docs/website/.astro`
- removed old snapshot/archive workspace data

Reason:

- these folders are generated, local, or stale and should not define the source layout

### Stale docs and scripts

- removed build/install/archive/script docs tied to the deleted plugin workflow
- removed stale docs website source that documented the deleted mod-kit structure
- reduced `tools/automation/` to the active utilities used by the current project direction

## Result

The remaining repository is now intentionally scoped to:

- the Rust game runtime
- the in-game editor/debug overlay
- the web editor foundation
- the shared content/assets/spec documentation for those systems
