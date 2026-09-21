# Havenwild B48R28C16R11 — experimental publication JSON repair

**Lane:** experimental; **base:** installed R10. This cumulative overwrite ZIP carries
all R10 source payload entries and an R11 bridge/test update. No production renderer,
asset mappings, elevation policy or game runtime is changed.

## Observed failure and preserved progress

The user-provided 2026-09-21 diagnostics show native PCC Full Gate GREEN for R10,
local HEAD `2bce6dc5742460783ec14194a59614d34c38821a`, and matching
`last-green-quality-gate.json.committedCommit`. The staging area is empty;
`publishedCommit` is blank. **The local certified commit succeeded; only
publication/reconciliation remains.** The generic 9-second PCC job receipt
contained only exit code 1 and did not itself prove which step failed.

## Defect and fix

R10 `GitSourceControl.ps1` calls `HavenwildGateAuthority.py git --action Status`
then `ConvertFrom-Json` on its human-readable status output. The CLI's
`frontdoor --root` is the existing structured JSON endpoint. R11 corrects the
call and verifies schema, exact HEAD, gate ID, full governed-source match and
empty staging area before a non-force push. Its branch/marker guards, remote
fetch/HEAD equality checks and native `ReconcilePublishedLane.py` remain intact.
The PowerShell bridge also prints the underlying publication failure message
rather than only surfacing a generic command exit.

## Recovery versus future fix

**To publish the already-committed R10 without invalidating its GREEN gate:**
use the separate `Havenwild_R10_Publish_Recovery.py` *from Downloads*, not the
repository root. It binds the verified R10 HEAD and gate ID; uses existing
`HavenwildGateAuthority.certify_matches` and
`ReconcilePublishedGreen.governed_paths_match_head` before any Git transfer;
pushes non-force to `origin/experimental`; verifies remote HEAD; and delegates
receipt writing to the existing `ReconcilePublishedLane.py`. It neither edits
Havenwild source nor manufactures a receipt. Only use it for this exact R10
checkout; refusal on changed HEAD/gate is intentional.

Apply this R11 root-drop patch **after** publishing R10 if desired. Applying R11
changes governed source, so run a fresh R11 Full Gate and use the native PCC
Commit + Push action; do not reuse R10's GREEN result. Failure to reach origin
(authentication, network, remote divergence) still blocks publication.

## Verification scope

Python regression tests and ZIP integrity can be checked in the packaging
container. A Windows PowerShell 5.1 native run, the complete Windows PCC gate,
and live remote publication must be verified in the user's Windows checkout.
