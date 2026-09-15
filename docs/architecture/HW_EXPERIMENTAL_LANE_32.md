# HW-EXPERIMENTAL-LANE-32

Status: protected Experimental publication bridge.

## Purpose

HW-31 established `experimental` as the active Havenwild development lane while `main` remains the certified stable baseline. The pre-existing protected source-control authority still hard-coded publication and pull operations to `main`. HW-32 closes that immediate safety gap without weakening Main protection.

## Behavior

When the active Git branch is `experimental`:

- `CommitPushGreen` first invokes the existing canonical GREEN authority for certified staging/commit, then pushes only `origin/experimental`.
- `Push` publishes only `origin/experimental`.
- `Pull` performs fast-forward-only pull from `origin/experimental`.
- publication requires a PASS Full Quality Gate whose `gitBranchAtGate` is exactly `experimental`.
- post-push reconciliation proves `origin/experimental == HEAD`, verifies governed source against the GREEN marker, verifies governed files match HEAD, and records `publishedBranch=experimental`.
- Main is never moved by this lane-specific path.

Main retains the historical protected publication route.

Repository setup/adoption/repair is deliberately blocked while Experimental is active because the current repair authority is Main-oriented.

## Follow-up

HW-33 generalizes front-door status, patch intake, package manifests, Forge adapter lane exposure, and Main mutation protection so every project operation is lane-aware rather than only protected publication.
