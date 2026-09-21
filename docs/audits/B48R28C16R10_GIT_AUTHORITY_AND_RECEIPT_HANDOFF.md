# Havenwild B48R28C16R10 — governed source/Git hygiene and PCC publication

**Lane:** experimental. **Base:** installed B48R28C16R9 source on the same local experimental test checkout. This is an overwrite-capable **source-only** PCC root-drop patch, not a complete rollup or a new repository. The existing native PCC remains sole build, gate, patch and source-publication authority.

## Root-cause evidence from the R9 focused handoff

- The canonical gate marker was `PASS`, run `QG-20260921-011915-ed8df741`, and its `governedPaths` included `.forgepy/cache/` and the isolated Bevy candidate's nested `target/`. Its source path count was 9,519. This is not evidence that generated output ought to be source-controlled.
- ForgePY generic `commit_green()` read **only** `.forgepy/state/last-green.json`, which is absent in the provided handoff, and would then perform generic `git add -A`/`git commit` if available. It never read the canonical Havenwild marker. That explains the `No GREEN receipt` message without implying the native PCC gate failed.
- The ForgePY GUI Dashboard already used the native `source-control.commit-push-green` operation, but the Git tab still exposed the generic `commit-green` and `push` entry points. This was a genuine, directly verified divergence.
- The R9 quick certification receipt hashed the Git porcelain output itself. The user safely unstaged generated outputs after the gate, so its fingerprint changed despite keeping all working files; the resulting `STALE` is explainable from receipt bookkeeping, not independently evidence of source edits. Source edits still require a new full gate.
- Two ~48,000-line full-source audit manifests are **retained**: `tools/handoff/Verify-FullSource.py` explicitly consumes the R2 manifest. They are separate from the accidentally staged Cargo output. The Bevy `Cargo.lock` is retained for locked dependency reproduction.

## R10 change contract

1. Align the authority's recursive tree-walk with `.gitignore`: exclude nested `target/`/Python caches, ForgePY volatile state/cache, and candidate-generated `evidence/` *before* applying broad `tools/build/` keep rules. Preserve `.forgepy/gui`, `.forgepy/runtime`, ForgePY package configuration, authored Bevy tests/sources, and credited source art.
2. Protect staging: check canonical full governed-tree fingerprint, branch and source manifest; reject unrelated pre-staged paths before mutation; retire **only** the approved generated path families from Git's index using `git rm -f --cached`, never delete local files; explicitly stage the certified paths; verify that no generated blob remains staged; recheck canonical fingerprint. An unrelated staged change blocks commit with a specific path diagnostic.
3. Keep the quick state a **read-only hint**, now based on changed source paths/content plus HEAD and canonical marker fingerprint, not volatile Git index status or evidence bytes. This does not replace `HavenwildGateAuthority.certify_matches` at commit. A new gate is required after R10 updates authority/source.
4. Both GUI Git and Dashboard publication call `publish_green()` and the exact existing `source-control.commit-push-green` PCC action. In Havenwild, generic ForgePY CLI `commit-green` and `push` explicitly block without Git side effects. No green JSON file is manufactured or copied between providers.
5. Preserve standalone ForgePY donor lineage and update only the Havenwild-local integration version, runtime lock, package provenance and integrity hashes for touched local package files.

## Application and one Windows certification checkpoint

Close ForgePY and Bevy. Put **only this patch ZIP** in the Havenwild experimental test checkout root. Launch the **existing** `HavenwildTools.cmd`, approve patch intake and select `FULL QUALITY GATE`. It must finish GREEN **after R10 is applied**; R9's prior marker must not be reused. Refresh the GUI; inspect the PCC GREEN/quick receipt status, then choose `Commit + Push Current GREEN` through the PCC, not generic Git. The experimental push additionally requires a committed HEAD matching the canonical marker, a fresh full governed-source verification with explicit JSON `gateState=GREEN` and `publicationEligible=true` (Status exits zero even when stale), and an empty staged index *before* transferring anything to origin. The PCC will retire tracked generated index entries only after matching the R10 canonical snapshot. `--cached` leaves working files, but makes a one-time recorded deletion of previously committed volatile paths if any exist. Review the final Git history and upstream comparison through the PCC.

If a gate fails, preserve the debug bundle and do not publish. If an unrelated staged path blocks publication, inspect/unstage that named path deliberately rather than running broad resets. If a concurrent GUI/gate writes to source after certification, the native authority will block until recertified.

## Verification scope

In a small isolated Git test repository the R10 source-only index behavior passed eight regressions, including safeguarding staged unrelated paths, preserving local generated files, rejecting generic ForgePY commit/push, and distinguishing index churn from a source edit. Existing 24 ForgePY GUI/console tests passed in the focused handoff. Candidate's 103-test suite **cannot be fully rerun from this intentionally focused archive** because its original full project content and pinned role-binding/world fixture files are absent (51 fixture-related errors, 2 skipped). Windows PowerShell, Cargo compilation, complete 9,519-path source fingerprint, source-mapping parity, GPU runtime and GitHub publication are not certified here. Only a new Windows PCC gate on the real checkout can supply the required evidence.

**Out of scope:** replacing Macroquad, migrating one-level elevation logic, promoting unapproved ElizaWy tiles, resolving Vulkan VUIDs, claiming Bevy runtime/PIE parity, removing legitimate full-source manifests, or publishing code automatically.
