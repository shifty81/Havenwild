# Havenwild Rename Notes

Generated: 2026-06-05

## Locked Identity

- Game / project name: **Havenwild**
- Main island / world identity: **Havenwild**
- Former working names archived: `TClone`, `Tavern Tweaker`, `Hearth & Hollow`, `Travellers Rest Clone`

## Rename Scope Applied

- Active Rust crates were renamed from `hearth_*` to `haven_*`.
- Old `tavern_*` compatibility/wrapper crates were moved out of the active workspace to `WORKSPACE/archive/legacy-duplicate-crates/`.
- The active workspace now includes only `haven_*` crates.
- Visible docs/schema identifiers were updated from `hearth_hollow` / `TClone` wording to `havenwild` where safe.
- Gameplay terms such as tavern, tavern interior, tavern staff, tavern customers, and tavern gameplay were intentionally preserved because they describe the game systems, not the old project identity.

## Forward Naming

Suggested active crates:

```text
haven_core
haven_world
haven_gen     # to be added when PCG worldgen is split out
haven_assets
haven_render
haven_sim
haven_net
haven_save
haven_editor
haven_game
haven_tools
```

Suggested file extensions:

```text
.hwsave
.hwworld
.hwasset.json
.hwscene.json
```

## Current Caveat

This rename package was transformed without running `cargo check` in this environment because Rust/Cargo is not installed here. Run `cargo check --workspace` locally after extracting.
