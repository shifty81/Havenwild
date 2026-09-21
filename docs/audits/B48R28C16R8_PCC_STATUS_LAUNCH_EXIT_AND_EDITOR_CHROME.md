# B48R28C16R8 — candidate launch receipts, PCC dashboard parity and editor chrome

## Baseline and evidence

Cumulative on the full B48R26→B48R28C16R7 series, experimental only. The user's Windows R7 full gate reached `GREEN PASS: B48R28C16R7`, including the isolated Bevy Cargo check, and the candidate launched with an actual Vulkan adapter and displayed original source pixels. This establishes a working launch/preview, **not** source-art review, gameplay viewport parity or Play-in-Editor. The R8 changes have NOT been built on Windows or passed a Windows full gate.

The user's `Pasted text(20260920-153138).txt` launch/close transcript shows:
- `15:16:07` selected NVIDIA GTX 1080 Ti / Vulkan, then validation starts `15:16:09`, immediately after opening the window;
- presentation-layout VUID `VkPresentInfoKHR-pImageIndices-01430` and acquire-semaphore VUID `vkAcquireNextImageKHR-semaphore-01286` are real Vulkan validation errors and should not be dismissed as a shutdown message;
- window closure is at `15:31:10`; candidate Python `cargo_attempt.json` recorded exit code 0 after close;
- PCC still printed `FAIL ... Command exited with code { JSON, logs, ... } 0`, a separate PowerShell success-stream/exit-code mixing defect.

Do not imply that exit code 0 certifies GPU correctness. Retain the present/acquire errors as an open P0 graphics diagnostic. Do not turn off Vulkan validation, force a different backend or change rendering synchronization without a controlled Windows A/B run and exact adapter/backend receipt.

## Implemented (bounded first M1 stabilization pass)

1. `tools/control/PccCommandHost.ps1`: the experimental Bevy child writes all output through `Write-Host` while forwarding stdout/stderr. The function returns only its numeric `$LASTEXITCODE`, like the existing legacy command path. The PCC job no longer receives the JSON transcript as its supposed exit status. No change to PCC patch application or full-gate authority.
2. `.forgepy/gui/pcc_gui.py`: new `dashboard_certification` renders the badge and certification card from the same `PccQuickState.py` gateState used by the guarded publication button. Generic ForgePY `lastGate` remains visible **as a separate diagnostic**, never overriding a newer Havenwild GREEN or promoting a stale/other-lane receipt. Missing/invalid quick state shows PCC UNAVAILABLE, never fabricated GREEN.
3. `.forgepy` local U5-derived integration version is updated to `havenwild.c16r8`, while explicitly retaining its U5 donor identity. Package manifest, provenance, runtime lock and README have matching hashes/identity.
4. `experiments/haven_bevy_candidate/src/main.rs`: explicit horizontal menu row (File/View/Help) and a 150 px default, resizable diagnostic dock instead of the generic 320 px default consuming most of the center view. Keeps the source-exact preview read-only, existing renderer and art approval boundaries intact.
5. Regression tests cover the status display precedence, fail-closed publication on stale/absent PCC state, the candidate stdout/exit pipeline, and horizontal menus/bottom-dock sizing.

## Verification here

- Bevy candidate Python suite: 91 passed (the suite uses reference-only copies of the original B48R26 real river fixture, mapping and PCC authority, NOT packaged in this cumulative patch).
- ForgePY GUI/console suite: 24 passed.
- Architecture suite: 20 tests, 1 expected isolated-checkout skip.
- Mapper suite: 7 passed.
- ForgePY package verification: passed, 0 failures. ForgePY runtime self-test: passed.
- Python syntax: passed. No Rust toolchain, PowerShell, Windows GPU or full PCC gate in this environment. Rust menu and dock changes are **uncompiled** here.

## Windows acceptance and next implementation boundary

Apply only this cumulative R8 ZIP via HavenwildTools to the `experimental` test checkout. Restart ForgePY GUI, run Full Quality Gate once, and confirm that the banner, certification card and guarded publication button describe the same R8 PCC state. Run `Run & Play → 6`, confirm horizontal menus, a larger central view and that the ending PCC job reports the **integer** exit code. Capture the Vulkan validation messages and full debug bundle if they recur; treat them as open even when the process exits zero. Do not push this disposable test folder or promote renderer/art/PIE claims until the respective evidence exists.

Next controlled GPU pass: identify whether the issue reproduces with the candidate's simple primary window/primary GUI camera only versus the added offscreen camera targets, inspect Bevy/wgpu swapchain lifecycle and adapter logs, and verify Vulkan versus a separately configured Windows backend if supported. Then move toward a real viewport-owned camera/target resize and shared Rust scene documents. Do not replace the existing Atlas Mapper or copy the old +1 elevation restrictions into the Bevy lane.
