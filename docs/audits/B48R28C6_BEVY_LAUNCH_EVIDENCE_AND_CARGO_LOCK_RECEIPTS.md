# B48R28C6 — Bevy launch evidence and locally resolved Cargo lock receipts

**Lane:** `experimental` only. **Last GitHub GREEN anchor:** B48R28C4, `d9c01b26ec2440f97fc1f6167ee561bc6d43e86e`. **Immediate predecessor:** unverified C5 compilation fix. This is a **self-contained cumulative PCC root-drop patch B48R26 → B48R28C6**, superseding C5; NOT a full source rollup.

## Why this pass

C4 repaired automatic source staging. The real user's Windows attempt subsequently resolved Cargo dependencies and reached one E0308 compiler failure, repaired in C5, but no subsequent Windows compile/GPU execution evidence has been provided. The C5 standalone Cargo workspace leaves `Cargo.lock` ignored and does not record a structured Cargo result; the GUI assumes source artwork is ready merely because an asset handle and render target exist. C6 addresses those diagnostic and repeatability gaps without changing canonical game/editor data.

## Actual code changes

- `experiments/haven_bevy_candidate/src/main.rs`: load the *single immutable original* summer atlas through one strongly retained `Handle<Image>` for both source-preview and 1,120-draft-sprite render paths. Add `report_original_sheet` scheduled immediately before the ForgeGUI UI: the GUI and console distinguish pending asset load, decoded pinned 512×832 image available in Bevy's CPU asset storage, and decoded-size mismatch. Text explicitly says that CPU image readiness **does not establish GPU output, screen pixels, renderer parity or source-art approval**. The existing unapproved mapping and semantic views remain; no pixel synthesis, source mutation or project writes. Surface headers accurately label C6.
- `experiments/haven_bevy_candidate/tools/candidate_gate.py`: inspect a candidate-local `Cargo.lock` as TOML, verify its pinned Bevy 0.19.0 / bevy_egui 0.42.0 entries and fail closed on malformed/symlinked locks. Use Cargo `--locked` when resolution exists; when absent, truthfully say first Cargo run will resolve dependencies (do not fabricate a lockfile). After Cargo returns, atomically write `experiments/haven_bevy_candidate/evidence/cargo_attempt.json` with exact command, exit code, source/fixture/manifest SHA-256, branch lineage, lock SHA before/after, and explicit GPU/PCC non-certification. Error 101 remains a failure; even exit 0 from `cargo run` is not claimed as a verified image. Evidence stays ignored inside the candidate and does not replace PCC job receipts or Full Gate.
- Tests updated for the shared atlas handle and new readiness contract; new negative tests cover nonzero Cargo result, generated lock hashing, `--locked` reuse, malformed/symlinked lock, and symlinked attempt receipt.

## What to do on Windows

1. Place only the unextracted **C6 cumulative** ZIP into Havenwild project root on `experimental`. Do **not** apply C5 separately.
2. Launch existing PCC and apply updates; run **Full Quality Gate**. If it fails, use PCC debug bundle rather than committing.
3. **Run & Play → Bevy candidate: run isolated preview** (or Build & Verify → Bevy candidate: cargo check). If it exits, attach the PCC action output and the ignored candidate `evidence/cargo_attempt.json` (only if generated). If the app opens, inspect the **River Scene (GPU DRAFT UNAPPROVED)** tab, **Bevy Original Source View**, and **Activity / Parity**, and share a screenshot of the real window for visual review. Image readiness text should say `READY ... CPU asset only`, but even READY is not pixel-level GPU evidence. Check the Inspector selection in both world diagnostic views and float its window.
4. After an actual *successful* Cargo resolution and application review, the generated `Cargo.lock` should be deliberately versioned through a subsequent PCC-governed pass; this ZIP does not invent and cannot certify the Windows-generated 615-package lock. It intentionally remains `.gitignore`d during the present launch test.

## Boundary / next milestone

C6 does **not** build Rust/Windows here; tools unavailable in this execution environment. No GPU or PIE proof, source-exact ElizaWy tile role approval, water/cliff adjacency, gameplay renderer integration, Macroquad retirement, or new GREEN claim. C5's root-Ui fix is still pending the user's actual Windows compiler result. The next implementation after the window successfully displays pixels is mapper-owned, reviewed ElizaWy export into a renderer-neutral draw plan; historical first-cell tile choices cannot be promoted by running the renderer.
