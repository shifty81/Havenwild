# Havenwild Experimental — HW-36 through HW-45

This cumulative batch establishes the second-generation Havenwild Project Control Center shell on the `experimental` lane. The existing mature `HavenwildTools.ps1` implementation remains the command execution backend while the new lightweight host owns orchestration and UI flow.

## HW-36 — One-shot PCC restart authority

- Replaces nested synchronous interactive PowerShell self-restarts with a single-consumer restart ticket.
- A gate interrupted by a PCC self-update resumes the same gate under the replacement source; noninteractive callers wait for its actual result.
- Empty/EOF menu input exits rather than endlessly redrawing `Unknown menu option`.
- Branch switches restart exactly once so newly checked-out tooling is loaded.

## HW-37 — Lane-aware patch preflight

- Reads `targetLane` / `targetBranch` from root-patch manifests and equivalent text-patch headers.
- Runs lane preflight before project mutation.
- Allows governed Main -> Experimental transfer through the existing lane authority.
- Never automatically switches Experimental -> Main.

## HW-38 — Patch-state ledger and gate blocker

- Adds PENDING / APPLIED / FAILED / DEFERRED state.
- Applied-versus-failed state is proven from the transactional archive destinations, not inferred only from process exit code.
- Required failed patches block Full/Fast Gate until resolved.
- Patch history is machine-readable under `.havenwild/pcc/`.

## HW-39 — Fast PCC front door

- Header/status uses cheap Git, marker metadata, and a quick-certification receipt.
- After a successful Full Gate, only Git-changed paths are content-hashed for fast post-gate verification.
- No recursive governed-source hashing during ordinary menu redraws.
- Full hashing remains part of certification/publication.
- Remote-tracking comparison is branch-aware (`origin/<active branch>`).

## HW-40 — Registry-backed shell normalization

- New shell builds menus from the existing project command registry.
- Stable command keys remain authoritative.
- Mature command implementations are reused rather than duplicated.

## HW-41 — Structured job authority

- Every shell-dispatched operation writes a compact job receipt.
- Latest operation/result/duration appears in the PCC header.
- Jobs remain local project operational state rather than source authority.

## HW-42 — ForgePY PCC provider parity

- Adds a project-native provider surface for status, gates, lane toggle, patch state and capability discovery.
- ForgePY remains a universal caller; Havenwild retains operational authority.

## HW-43 — Havenwild tooling profile

- Defines the integrated Havenwild studios and shared editor services.
- Keeps game-specific semantics in Havenwild while mirroring Ember capability boundaries.

## HW-44 — Unified workflow boundary

- Root launcher enters one shell.
- Patch intake happens before gates.
- Gate and publication stay project-owned.
- Lane switching and restart handoffs are explicit and bounded.

## HW-45 — PCC v2 certification contract

- Adds `Validate-HavenwildPccV2.py`.
- Validates the shell, restart, intake, quick-status, capability and editor-tooling contracts before a v2-hosted gate runs.

## Resulting workflow

`HavenwildTools.cmd -> HavenwildPccHost.ps1 -> stable command registry -> HavenwildTools.ps1 backend / project authorities`

This deliberately avoids a destructive rewrite of the mature PCC command implementation while giving Havenwild the same modular shell/provider/jobs/intake boundaries targeted for the Ember ecosystem.
