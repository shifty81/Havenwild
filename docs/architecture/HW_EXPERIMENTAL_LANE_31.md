# HW-EXPERIMENTAL-LANE-31

Status: Experimental architecture bootstrap.

## Authority

Havenwild now uses two explicit Git lanes:

- `main` — last certified stable baseline.
- `experimental` — active forward-development lane.

The Git branch is the authority. `.havenwild/development-lane.json` is generated supporting state only.

Experimental was forked from certified GREEN commit:

`5fb9824e6779eb16c51f3ee1a22dd9ef17a8f332`

## Policy

Routine Havenwild development occurs on `experimental` until the user explicitly authorizes cutover.

Main must remain available for build/test/run/diagnostics and recovery, but routine development, patch application and arbitrary development commits are policy-blocked. Enforcement is being wired into the PCC/update/source-control authorities in the immediately following Experimental passes.

Cutover is never automatic. It requires:

1. clean Experimental source;
2. GREEN Experimental Full Quality Gate;
3. Experimental -> Main comparison;
4. explicit user authorization;
5. governed Main cutover;
6. post-cutover Main Full Quality Gate before Main is considered the new certified baseline.

## Lane authority

`tools/control/DevelopmentLane.ps1` provides the initial lane authority:

- `Status`
- `SwitchExperimental`
- `CompareMain`
- `PrepareCutover`

`PrepareCutover` writes a local plan only. It never mutates Main.

`tools/control/ProjectStatus.ps1` now surfaces lane state directly.

## Follow-up

HW-32 through HW-34 complete the enforcement layer:

- PCC/header and GREEN gate lane awareness;
- protected Experimental commit/push and Main protection;
- root-patch intake lane rejection;
- lane-aware package/artifact manifests and lineage;
- ForgePY lane command exposure.

No ForgeGUI/editor migration begins until this lane boundary is operational.
