# B48R28C3 — Original ElizaWy pixels reach the Bevy GPU draft viewport (NOT certification)

## Source and operational baseline

- GitHub `shifty81/Havenwild` `experimental` HEAD verified at `78ff838499015ff434dbd935ae5daf9cbd11a02e`, commit message `B48R28B - certified GREEN`. R28C1 and R28C2 are uncommitted cumulative handoffs. This superseding **cumulative** B48R26–R28C3 patch retains all R28C2 payload and uses B48R28B GREEN as its Git baseline; NOT a full-source rollup, NOT a new independently certified GREEN gate.
- Original source `Terrain/terrain_summer.png` SHA-256 `1251a6ea556330190ccb1e3af166eb69fbec4b7a3f7d51c1f54728abd75bd752`, staged read-only from original `Terrain.zip`. Existing 40×28 river acceptance fixture remains canonical and untouched.
- The historical `content/assets/intake/lpc_terrain_family_mapping_v0_3.json` SHA-256 is `280735da3be341cbbb6a085d45fc14673886a94d24d2b34473ff48878f038307`. Its historical `baseTiles` are **not certified** and never reused as published recipes.

## Concrete delivery

1. A candidate-only explicit binding document `content/architecture/havenwild_bevy_draft_role_bindings_v0_1.json` records three manual experimental role-to-existing-historical-tile choices: Grass → grass variant 0, RiverWater → river_water variant 0, MudBank → mud_bank variant 0. It is deliberately branded DRAFT, with `sourceArtApproval=false`, `worldRendererParity=false`, `runtimePublicationAllowed=false`, no adjacency/autotile/height/collision/animation inferences. This is experiment configuration, not a new asset catalog or approved mapper export.
2. `draft_source_draw_plan.py` consumes the SAME PCC-verified original source and semantic fixture, checks pinned historical-mapping hash and exact role bindings, validates all 1,120 historical 32×32 source rectangles against the original 512×832 atlas, and writes only `experiments/haven_bevy_candidate/evidence/draft_source_draw_plan.json` using atomic replacement. The result has 1,120 **unreviewed** draw entries and **zero approved** draw calls; missing or changed roles fail closed. It does not generate PNG output, modify an original asset, approve a recipe, or write game saves.
3. Candidate Rust independently rechecks source PNG and credits, original fixture and semantic receipt, historical mapping hash, bindings hash, and the 1,120 per-cell source rectangles before startup. Its new Bevy renderer path allocates a dedicated 1280×896 offscreen target, uses the original sheet as a `TextureAtlasLayout` and renders 1,120 sprite cells to the `River Scene (GPU DRAFT UNAPPROVED)` ForgeGUI tab; the source sheet tab and semantic diagnostic tab remain. World picking in this draft updates the existing inspector's world selection but does not edit the world. This is implementation code, not evidence that Rust/GPU has successfully compiled or launched.
4. The existing PCC registers **one** additional command, `experimental.bevy.draft-plan`, through the same extension registry, dispatcher and job host. Existing Build/Run now generate the draft evidence after source and semantic gates and before invoking the isolated Cargo workspace. No new root launcher/PCC, source database, canonical save or production build graph.
5. Added Python tests for deterministic exact addresses, mismatch failures, source bounds, non-approval flags, atomic candidate-only evidence, symlink refusal and the actual archived historical mapping and river fixture when present.

## Visual limitation — deliberate and important

These sprites come from actual original pixels, **but the composition is not visually correct/certified**. Choosing one static base source cell per semantic role does not resolve shore edges, Wang corners, mixed terrain, modular rivers, cliff ends, waterfall direction/width, elevation, collision, or animation. It may look blocky/repetitive and must not be used as a summer reference board or runtime comparison screenshot. Any screenshot must be labeled `UNAPPROVED HISTORICAL GPU DRAFT`. Approval belongs only to the original Asset World Mapping Workspace → source-specific review receipts → Havenwild Asset Authority, followed by validation and an actual editor/client parity gate.

## Existing PCC workflow (experimental branch only)

Use only this latest cumulative ZIP; do not stack C1/C2/C3. On a real project checkout, stage `Terrain.zip` with the existing candidate source preparation if not already staged. Run the existing PCC commands in sequence: `experimental.bevy.verify` → `experimental.bevy.scene-plan` → `experimental.bevy.draft-plan` → `experimental.bevy.build` → `experimental.bevy.run`. Build/Run also regenerate the plan themselves; no manual plan is necessary. `cargo check`/run will require Rust >=1.95 and pinned Bevy/ForgeGUI dependencies.

Do not commit GREEN unless the existing PCC Full Quality Gate actually passes on Windows; launch and inspect the original atlas, semantic map and GPU DRAFT tab and capture real GPU/debug receipts. The source ZIP remains outside patch transport; candidate evidence is ignored from Git.

## Bounded next implementation, without duplicate authority

- **R28C4:** Use the existing Atlas Mapper's project documents and original sheet stack to author complete, reviewable role/adjacency/river-bank/cliff recipes. Export a draft recipe *through* the existing Asset Authority. Distinguish draft → reviewed board → validated → runtime certified; keep old V7 resolver separate and optional. Bevy must consume the same versioned source-exact plan as a legacy shadow renderer before parity is claimed.
- **R28D:** Editor world viewport + selection/commands + revisions/undo/save-reopen in disposable copy, then real host snapshot/PIE ACK, collision/nav and worldgen semantics, performance, Windows GPU, PCC Full Gate. Only retire Macroquad once game and editor use the replacement successfully.

## Verification status

Pure Python tests and source-data hash checks are runnable here. Rust toolchain, Windows graphics, actual PCC Full Gate and game runtime are not available here and have **NOT RUN**; neither visual approval, renderer parity, PIE, nor Macroquad retirement is claimed. This package changes only experimental candidate code/contracts/PCC extension wiring and docs, with **zero removals**; legacy renderer, original art, game and mapper remain unmodified.
