# Havenwild B48R28B — isolated Bevy / ForgeGUI source-preview candidate

**Candidate only. NOT the game, NOT the production World Editor, NOT a replacement renderer yet.** This optional app uses a real Bevy 0.19 off-screen render target containing the **original** `Terrain/terrain_summer.png` source sheet, displayed in the **actual pinned ForgeGUI shell** through `bevy_egui` 0.42 / egui 0.36. It reads the existing `terrain_acceptance/river_scene_v1.json` **semantics for evidence only**; it deliberately does not guess a mapping from semantic role to source pixels. Pixel selection inspects source coordinates only; there are no writes, fake edit commands, save or PIE actions.

This project is an independent `[workspace]`, **not** a Havenwild root workspace member. Current production editor, game, world, source registry, PCC and canonical saves are unchanged.

## Windows execution after applying cumulative root ZIP through the existing PCC

**B48R28C4:** Run & Play → Bevy candidate: run isolated preview now stages
the original ElizaWy summer sheet and Terrain/Credits.txt automatically when
the candidate has not yet been staged. It first reuses Havenwild's existing
`assets/source/licensed/lpc_revised/Terrain/` source, validating both pinned
SHA-256 values. If that dependency is not installed, it uses an explicit
`HAVENWILD_BEVY_TERRAIN_ZIP` path or a `Terrain.zip` already in the project root.
It never searches Downloads, downloads anything, changes source files, or
changes an existing receipt to conceal altered bytes. Automatic preparation
occurs only on **Build/Run**, after verifying the `experimental` branch and
B48R28B ancestry. Verify and Status stay read-only.

With the original source already installed, simply use the existing PCC
**Run & Play → Bevy candidate: run isolated preview**. If neither verified
installed source nor the project-local ZIP is available, explicitly stage the
original ZIP once with the command below or set the named environment variable.
The ZIP and original PNG are never embedded in the cumulative patch.

From the Havenwild repository root in PowerShell:

```powershell
py -3 experiments/haven_bevy_candidate/tools/prepare_source.py --terrain-zip "C:\path\to\original\Terrain.zip" # only needed when project source is absent
py -3 experiments/haven_bevy_candidate/tools/semantic_scene_plan.py --root . --write-candidate-evidence
cd experiments/haven_bevy_candidate
cargo +stable check
cargo +stable run
```

Rust compiler **at least 1.95** is required by pinned ForgeGUI. Source preparation validates a specific original source PNG SHA, ZIP integrity, exact fixture dimensions, and Git branch/ancestry when present. Assets and source-receipt data are staged **only** into `.gitignore`d candidate folders and never shipped in the PCC patch. With absent `.git` metadata, the receipt says so; it cannot claim Git or PCC certification. The application verifies the original hash and receipt again at startup and fails closed if missing.

## What this demonstrates (only if actually built and launched)

1. Real Bevy GPU render-to-image (512×832 source image) shown through ForgeGUI's center surface; nearest-neighbor source sampling.
2. ForgeGUI's registered Source Library, source preview, Inspector, Scene Semantics, Activity surfaces; use Dock to float Inspector and test window resize.
3. The immutable original ElizaWy PNG and the real Havenwild river acceptance scene are consumed as distinct, correctly labeled resources.
4. The Bevy candidate dependency graph is Macroquad-free (independent workspace; the root engine still uses Macroquad).

## What is NOT proven

World terrain resolver/certified art assembly; cliff/water semantics; editor document commands; selection in world coordinates; PIXEL/animation/prefab studio migration; integrated Play-in-Editor; full game; runtime parity; Windows build; PCC Full Gate; retirement of Macroquad. Do not promote the app or use its screenshot as an approved summer scene. Do not substitute `assets/generated/**` for original licensed art.

## Actual next two bounded passes

- **R28C:** feed canonical authored world document + certified terrain draw-plan into Bevy offscreen camera, implement coordinate-picking, ForgeGUI Inspector authoring commands with expected revision, undo/save/reopen in disposable scene copy. Preserve original source hashes.
- **R28D:** run actual Havenwild authoritative host and game through the same document snapshot, record scene/asset revision ACKs, collision, screenshots, performance, reset behavior and PCC Full Gate. Only then decide renderer promotion.

The actual prepared asset file is `assets/source/Terrain/terrain_summer.png`, staged from the user-supplied archive. `evidence/source_stage.json` is local candidate evidence, **not** an art-approval or gate receipt. No additional PCC entry was created: existing root-drop intake and Full Quality Gate remain the authority.

## B48R28C2 — actual fixture semantic view and renderer-neutral evidence (NOT an art render)

The candidate now opens a **River Scene (Semantic Debug)** center tab alongside the
original-source Bevy texture tab. It reads real fixture terrain cells, displays
explicit debug-role swatches, supports world-cell picking and an Inspector with
separate source-sheet and world-cell selections. No semantic-to-art mapping is
inferred: all 1,120 cells are reported UNMAPPED until the existing Mapper and
Asset Authority export reviewed source-exact recipes. Elevation, collision,
waterfall imagery, world renderer parity and PIE remain pending. The semantic
canvas is an egui diagnostic view; the original source preview uses Bevy's
GPU render target.

Run `experimental.bevy.scene-plan` through the existing PCC after source
preparation, or let Build/Run generate the identical candidate-only receipt.
This writes solely to ignored `experiments/haven_bevy_candidate/evidence/`.
Direct Cargo run now requires this receipt and rechecks its scene SHA, source
SHA, counts and exact per-cell semantics. No canonical file is ever updated.

## B48R28C1 — operations are now owned by the existing PCC

After staging the verified original source as described above, use the project's ROOT
PCC Build & Verify menu to run **Bevy candidate: source + fixture verify**, then
**Bevy candidate: cargo check**, or use Run & Play → **Bevy candidate: run isolated preview**.
The same registered command keys are available through the existing ForgePY/PCC provider:
`experimental.bevy.status`, `experimental.bevy.verify`,
`experimental.bevy.scene-plan`, `experimental.bevy.build`, `experimental.bevy.run`. The PCC, not the candidate, owns logs/jobs, Git and approval.

All mutating/rebuild operations are restricted to an `experimental` checkout descended
from B48R28B GREEN. The source-stage receipt must still match the staged original
PNG, credits, and the exact current fixture bytes. This work does **not** replace
Havenwild's world renderer, editor documents or gameplay PIE.

## B48R28C3 — Source-exact original-pixel GPU DRAFT (NOT visual approval)

Use existing PCC `experimental.bevy.draft-plan` (or Build/Run, which includes
the same compiler after the existing source/semantic verification). It reads
existing `content/assets/intake/lpc_terrain_family_mapping_v0_3.json` plus
`content/architecture/havenwild_bevy_draft_role_bindings_v0_1.json`. Their hashes
are pinned; the explicit bindings choose ONLY the first historical base tile for
Grass, RiverWater and MudBank. The candidate loads original `terrain_summer.png`
through Bevy as one tile atlas and renders 1,120 GPU sprite cells into a separate
offscreen world texture. No generated PNG atlas, invented source pixels, save,
mapper publication, V7 fallback, editor write or collision/nav inference occurs.
The GPU tab and inspector say **UNAPPROVED DRAFT**. The bank/river edges are
visually incorrect until actual adjacency recipes pass review. The semantic
debug tab and original source preview are retained separately. R28C3 only
proves the original source can reach a GPU world-shaped viewport: no certified
art, renderer parity, actual gameplay, PIE, Rust/Windows build or GREEN claim.

## B48R28C7–C16 — integrated infrastructure, still experimental

`tools/experiment_spine.py` is the candidate-only implementation of project-context verification, read-only source stack, isolated scene document, revisioned terrain edit commands, replayable undo/redo, atomic candidate-only save/reopen, mapper topology review queue, renderer-neutral *historical/unapproved* packets, sealed PIE **metadata ticket only**, semantic diff, and fail-closed readiness report. It calls the established `candidate_gate.py` for project identity, experimental-branch ancestry, source bytes, credits, and fixture integrity. It does **not** create a new PCC, runtime server, mapper, asset catalog, or game save.

Use the existing PCC's `experimental.bevy.infra-*` registered operations for source stack, isolated document open, mapper queue, render packets, snapshot save/reopen, PIE ticket and readiness audit. Open the candidate's **Infrastructure / Evidence** ForgeGUI surface and click its read-only refresh button after the PCC audit. All generated infrastructure receipts live under ignored `evidence/infrastructure/`; no original artwork, authoring mapping, production save, or source fixture is altered. For API-level tests, the CLI supports `edit --command-id ... --revision ... --x ... --y ... --role ...` plus `undo` and `redo`, always against the isolated session only. That CLI is a candidate command API, **not an integrated editor brush**.

The protected `main` lane retains its existing gate. On `experimental` with this candidate present, the **normal Havenwild Full Quality Gate** now requires the candidate Python suites and `cargo check`, then runs its unpromoted readiness audit *before* writing GREEN. Earlier C4 GREEN did not compile the experimental candidate; this closes that certification gap, but a successful `cargo check` alone is still not a GPU screenshot, visual art approval, gameplay PIE, or renderer parity. Any candidate test/compiler failure blocks the new gate and triggers the PCC's standard diagnostics. Direct `Run` still requires a separate runtime/visual check.

No automatic snapshot open, edit, mapping certification, or PIE launch occurs when the full gate runs. That is intentional: a build gate must not silently mutate authored documents or invent approval. Missing approved recipes and absent runtime acknowledgements remain explicit blockers. Full detailed acceptance criteria and the ten-slice completion ledger are in `docs/audits/B48R28C16_TEN_PASS_EXPERIMENTAL_INFRASTRUCTURE_HANDOFF.md`.

## B48R28C16R9 — world viewport presentation and controlled GPU comparison (EXPERIMENTAL)

The river GPU draft now fills the available center dock with *presentation-side* pan (right/middle drag), cursor-anchored wheel zoom, Fit, optional grid and exact cell picking. It retains a fixed 1280×896 Bevy offscreen texture; dynamic render-target allocation, chunked game world, certified source mapping and playable PIE remain future integrations. The Inspector shows actual selected fixture role plus NESW neighbor roles, not published visual recipes. No scene/source writes occur.

Vulkan VUIDs `VkPresentInfoKHR-pImageIndices-01430` and `vkAcquireNextImageKHR-semaphore-01286` were observed at startup on the Windows test machine, also reported on minimal upstream Bevy/wgpu applications. Do not infer they are an ElizaWy sprite error; do not silence validation or claim resolved. Use the same Havenwild PCC Run & Play commands: normal auto backend, DX12 full candidate, primary-window-only automatic backend, and primary-window-only DX12. For the diagnostic modes, the primary-only startup bypasses **both** offscreen targets and all river sprites while retaining the pinned source verification and ForgeGUI shell. The exact requested mode appears in candidate `evidence/cargo_attempt.json`; the **actual adapter/backend must be read from Bevy's AdapterInfo log**, not assumed from a requested value. All four runs must exit zero and must be visually inspected before considering renderer validation clean. The candidate run's zero exit code never certifies GPU correctness.

If the full candidate yields Vulkan errors but the primary-only Vulkan probe does not, inspect offscreen cameras/target composition. If both have errors, investigate Bevy/wgpu/driver first. If DX12 also errors, capture the exact backend and driver details rather than silently switching production. This is differential diagnosis only; the first renderer parity / gameplay acceptance gates remain BLOCKED.
