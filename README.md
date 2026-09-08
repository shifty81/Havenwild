# Havenwild

Havenwild is the standalone Rust game project and native authoring environment in this repository.

## Current project authority

- `docs/current/` contains the current development handoff, roadmap, repository rules, validation architecture, and packaging guidance.
- `docs/source_of_truth/HAVENWILD_PROJECT_SOURCE_OF_TRUTH_REGENERATED.md` contains the consolidated project direction and architecture.
- Historical pass notes and implementation evidence belong under `docs/archive/` or `docs/handoffs/`, not at repository root.

## Project Control Center

Run `HavenwildTools.cmd` for the compact project control interface.

The recommended verification path is:

1. **Build & Verify**
2. **Full quality gate**

The quality gate runs root cleanliness, the full workspace build, and the complete test suite in sequence.

## Root policy

The repository root is intentionally minimal. The root-cleanliness validator permits only project metadata plus this README and `HavenwildTools.cmd`; generated reports, patch notes, handoffs, logs, and validation evidence must live in their designated folders.
