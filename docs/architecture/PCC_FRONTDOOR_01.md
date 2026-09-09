# PCC-FRONTDOOR-01 — Havenwild Control Center Front Door

## Purpose

Make the two normal project operations the first two root-menu actions while preserving the proven Control Center commands underneath them.

1. **FULL QUALITY GATE / CERTIFY GREEN** runs the existing canonical Full Quality Gate.
2. **COMMIT + PUSH CURRENT GREEN** publishes only the exact governed source fingerprint certified by the current GREEN gate.

## Preserved commands

The previous root entries remain available, shifted down without replacement: Build & verify, Run & play, World/terrain/scene tools, Asset authority/catalog, Project maintenance/diagnostics, Packaging/baselines, Logs/help, Advanced/all commands, and Source control/GitHub.

## Header state

The root header now exposes separate human-facing identities for:

- `Local`: the currently accepted local patch/pass identity;
- `Repository`: the last known published patch identity (or commit fallback);
- `Sync`: MATCH, local-ahead GREEN unpublished, stale/modified, or other truthful state;
- `Gate`: GREEN, STALE, or no certification;
- `Updates`: pending governed root-patch count.

The canonical Git state remains visible separately.

## Publication safety

Root option 2 does not create a new publication implementation. It routes to the existing protected `CommitPushGreen` authority. Before publication it requires the current canonical GREEN record to match the governed-source fingerprint. A source change after certification therefore blocks publication and requires option 1 again.

Normal root publication uses the certified patch identity for a normalized commit message:

`Havenwild <PATCH> - certified GREEN`

Advanced/manual Git operations remain in the Source Control submenu.

## Repository identity continuity

Canonical GREEN finalization preserves `repositoryPassAtGate` when the previous GREEN record corresponds to the current HEAD. This lets the front door continue to display the repository baseline after a new local patch has been certified but before it has been committed.

## Architecture boundary

This pass is intentionally a routing/state presentation normalization. It does not replace:

- `Invoke-FullQualityGate`;
- `HavenwildGateAuthority.py` governed-source certification;
- `GitSourceControl.ps1`;
- root patch intake;
- debug bundle generation;
- command registry/menu providers.

Those remain the underlying authorities.
