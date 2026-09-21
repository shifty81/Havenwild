# Havenwild B48R28C7–C16: 10-slice experimental infrastructure handoff

## Authority and lineage

- Baseline GitHub `experimental`: B48R28C4 GREEN, commit `d9c01b26ec2440f97fc1f6167ee561bc6d43e86e` (as previously verified); C5/C6 were local unverified handoffs. This ZIP supersedes C6 and includes all 44 of its payload files (some overwritten with this batch), plus this batch's new files. It is a **cumulative root-drop patch from B48R26** and **not a complete repository source rollup**.
- Do not apply C5, C6, then C16 separately. Use this one cumulative ZIP through the existing experimental PCC. Original complete source remains in your already checked-out repo.
- All new candidate evidence is ignored under `experiments/haven_bevy_candidate/evidence/infrastructure`. `main`, original ElizaWy source PNG/credits, production scene JSON, runtime asset catalogs, production game/editor, canonical saves and estate remain untouched by the candidate infrastructure.
- Root Full Gate is modified for the **experimental branch only** to require the Bevy candidate's Python contracts, `cargo check`, and source/input readiness audit before GREEN. C4 could show GREEN even with a candidate compilation error because the previous root gate did not build the isolated workspace; this pass closes that hole. Neither a GREEN nor a successful Cargo check is by itself GPU visual parity or actual PIE proof.

## Ten bounded code slices

| Slice | Actual implementation | Proof and limitations |
|---|---|---|
| C7 | One project context backed by existing `candidate_gate.verify` and PCC; rooted, symlink-rejecting candidate evidence | Reject nonexperimental lineage; no secondary PCC or untracked authority. |
| C8 | Read-only immutable-source stack receipt with source + credits hashes | Does not certify ElizaWy visual role mapping. |
| C9 | Isolated river document created from the exact original source fixture and SHA | Subsequent open preserves edits rather than resetting; no production save writes. |
| C10 | `set_terrain` command, stable command IDs, expected-revision check, bounded coordinate/role constraints | CLI/API only, not a completed ForgeGUI brush. Reject duplicate/stale/no-op commands. |
| C11 | Bounded event journal, replay integrity, revisioned undo, redo and branch-after-undo | Refuses tampering and conflicting revisions. |
| C12 | Atomic single-file candidate save envelope + verified reopen | No partial JSON pair; cannot publish or overwrite original scene. |
| C13 | Existing mapper-facing queue of unique source-semantic NESW neighbor signatures | Covers all 1,120 scene cells; zero automatic source approval, no fabricated cliffs/waterfalls. |
| C14 | Renderer-neutral, per-cell source rectangle/depth/semantic packet model | Validates *existing historical* bindings/draft per cell; all 1,120 remain UNAPPROVED, elevation unknown rather than fabricated level 0. Not yet used as production renderer data. |
| C15 | Sealed candidate-only PIE snapshot metadata with SHA/revision, denied launch, absent runtime ACK | No actual headless simulation/game PIE claim. |
| C16 | Semantic diff/readiness detector, PCC registrations, ForgeGUI read-only Evidence panel, Full Gate candidate build enforcement | Full Gate now blocks candidate build failures; requires Windows run/screenshots and art approval separately. |

## PCC integration and execution sequence

The existing root `HavenwildTools.cmd` remains the only entry point. New registered operations are in `tools/control/PccCommandExtensions.ps1` and dispatch through existing `HavenwildBevyCandidate.ps1` to `tools/experiment_spine.py`. Standard job IDs, logs, debug bundle and transactional patch intake are unchanged.

For a bounded candidate infrastructure smoke test, after applying the patch on `experimental`: use `experimental.bevy.infra-source` (Asset Authority menu), `experimental.bevy.infra-open`, `experimental.bevy.infra-mapper`, `experimental.bevy.infra-packets` (World menu; C3 draft evidence must exist first), `experimental.bevy.infra-save`, `experimental.bevy.infra-reopen`, `experimental.bevy.infra-pie`, `experimental.bevy.infra-parity`, `experimental.bevy.infra-audit` (Build & Verify). Generate the historical draft first via existing `experimental.bevy.draft-plan` if needed. All operations refuse missing/altered source staging rather than silently inventing artwork.

The candidate API supports a deliberate isolated editing test directly from the repository root; replace the example ID when repeating a command, and advance `--revision` after each successful mutation:

```powershell
py -3 experiments/haven_bevy_candidate/tools/experiment_spine.py open --root .
py -3 experiments/haven_bevy_candidate/tools/experiment_spine.py edit --root . --command-id example-1 --revision 0 --x 0 --y 0 --role MudBank
py -3 experiments/haven_bevy_candidate/tools/experiment_spine.py undo --root . --revision 1
py -3 experiments/haven_bevy_candidate/tools/experiment_spine.py redo --root . --revision 2
py -3 experiments/haven_bevy_candidate/tools/experiment_spine.py save --root .
py -3 experiments/haven_bevy_candidate/tools/experiment_spine.py reopen --root .
```

This changes **only ignored experimental evidence**, not the actual `river_scene_v1.json`. If an existing isolated session has a newer revision, commands correctly fail with stale-revision rather than reset it. Full Gate does **not** make these edits automatically.

Run `Full Quality Gate` once the user chooses to build. On `experimental`, its mandatory candidate check may download/compile Bevy and will FAIL until any remaining Rust API/compiler problems are corrected. Running `Run & Play → Bevy candidate` is a **separate runtime smoke**, and any screenshot must label source view, semantic debug grid and original-pixel GPU draft correctly. Original-source artwork and credits are intentionally not included in the patch; C4 auto-staging reuses the project's verified installed source.

## Required evidence and remaining work

**Implemented/testable today in this handoff:** Python candidate domain contracts, isolated snapshot commands, JSON receipts, existing PCC command entries, read-only ForgeGUI evidence view, and a mandatory candidate build step in experimental Full Gate. Unit tests can run in a source checkout without the GPU; all package SHA-256 values are checked separately.

**Not implemented / not claimed:** a certified ElizaWy visual recipe for each river bank/shore; real north/south/east/west waterfall source proof; connected cliff geometry/height/collision/nav; Bevy consumption of the *new* renderer-neutral packets; ForgeGUI world-brush commands (CLI contract only); real client PIE and host ACK; automated image parity, sound/animation/network migration; absence of Macroquad from root graph; successful local Windows Rust build, GPU launch, PCC Full Gate or GREEN for this pass. C4 is the last user-confirmed GREEN anchor.

**Immediate next work after first build:** fix any concrete Cargo diagnostic (do not claim future compile results); demonstrate Bevy source/draft offscreen views through ForgeGUI; author ElizaWy recipes in the **existing** Atlas Mapper and publish them only via Havenwild Asset Authority with exact review evidence; feed published draw packets into both editor/game renderers; bind session command API to real GUI; implement a genuine disposable, server-authoritative PIE with snapshot ACK. Keep the historically unapproved draft separate throughout.
