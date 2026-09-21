# Havenwild B48R28C16R4 — PCC-governed dashboard and pytest collection repair

## What was observed

The supplied Windows ForgePY composite gate transcript confirms successful root `cargo check --workspace`, `cargo build --workspace`, and `cargo test --workspace`. The subsequent ForgePY root `python -m pytest -q` failed **during collection**, with `SystemExit: 0` at `tools/control/test_reconcile_held_duplicate.py:18`; no Python tests ran in that phase and the gate recorded exit 3. This is not a Rust build error or proof that the separately isolated Bevy candidate ran.

## Repairs

1. The bundled Havenwild ForgePY dashboard exposes `PCC FULL GATE` and `Commit + Push Current GREEN`. Both dispatch exact allowlisted keys to the **existing** `tools/control/HavenwildPccHost.ps1` via hidden, noninteractive PowerShell, with captured stdout/stderr, persistent GUI transcripts, exit codes and the existing cancellation path. No new Git staging, pushing, certification, or independent PCC service was implemented.
2. The GUI's worker fetches read-only certification from the existing `tools/control/PccQuickState.py` alongside the normal ForgePY snapshot. Dashboard publication requires an authorized `experimental` or `main` lane, `publicationEligible=true`, `gateState=GREEN`, `syncState=LOCAL_AHEAD_GREEN_UNPUBLISHED`, and a matching quick certification receipt if the worktree is modified. It is disabled during another job. The actual PCC rechecks the full governed fingerprint at publication; the UI is only a conservative readiness display.
3. Publish asks the user for confirmation, then delegates to `-Command source-control.commit-push-green`. The operation streams to the always-visible lower console and retains the GUI transcript. Already synchronized, stale, or unverified states do not expose an active publish button.
4. The historical exact-transport reconciliation regression now puts its fixture inside a test function, skips if the original historical transport is unavailable, and keeps standalone CLI execution via `if __name__ == '__main__'`. It never terminates pytest during module import and it does not synthesize substitute transport bytes.
5. The ForgePY package integrity manifest, runtime version/lock, provenance, documentation and dashboard regression tests are updated coherently.

## Boundaries and operation

- The main Havenwild game, source assets, real scene recipes, canonical PCC gate/publish implementation and upstream ForgePY donor remain unchanged.
- Apply this *single cumulative* ZIP through the existing Havenwild root intake. It includes all R3 payloads; **do not also apply R3**. After intake, restart ForgePY GUI to reload Python code, run `PCC FULL GATE` on the Dashboard, and only publish after the dashboard shows a current GREEN certification and outstanding changes.
- The generic ForgePY full scan remains available separately; the Dashboard now directs the primary Full Gate button to Havenwild's authoritative PCC to avoid presenting ForgePY's synthetic component gate as the canonical certification.
- Tests here validate Python source, protected dispatch and skip semantics; Windows PowerShell window visibility, GitHub publishing, GPU rendering, the authoritative PCC Full Quality Gate and the Bevy runtime are not certified by this patch authoring run.
