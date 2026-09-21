# B48R28C5 — First Windows candidate compile repair: egui root UI (E0308)

**Scope:** experimental only; cumulative overwrite from B48R26 through B48R28C5, superseding C4. Baseline: GitHub `experimental` B48R28C4 certified GREEN, `d9c01b26ec2440f97fc1f6167ee561bc6d43e86e`, verified from user's PCC report and GitHub branch. This transport is not a source rollup.

## Evidence received

The actual Run & Play → Bevy candidate execution successfully auto-staged and verified original ElizaWy summer terrain and credits, verified the 40×28 river fixture (1,120 cells), compiled its Rust dependencies and reached `haven_bevy_candidate`. The first actual compiler error is E0308 in `experiments/haven_bevy_candidate/src/main.rs:502`: `egui::CentralPanel::default().show(ctx, ...)` passes a `&mut egui::Context`, while egui 0.36.2 expects `&mut egui::Ui`. The process exited code 101. This proves neither successful candidate execution nor GPU rendering.

## Minimal source repair

`experiments/haven_bevy_candidate/src/main.rs`: create one `viewport_ui` using `egui::Ui::new(ctx.clone(), "havenwild.experimental.viewport".into(), egui::UiBuilder::new().layer_id(egui::LayerId::background()).max_rect(ctx.viewport_rect()))`. Pass `&mut viewport_ui` to `egui::CentralPanel::default().show`; keep `show_application_shell(root, ctx, ...)` in its existing parent-Ui/context ownership pattern. This follows `bevy_egui 0.42`'s official `examples/ui.rs` source for egui 0.36 root Ui construction: https://docs.rs/crate/bevy_egui/0.42.0/source/examples/ui.rs.

`experiments/haven_bevy_candidate/tests/test_egui_root_ui_contract.py`: three static regression tests prevent reintroducing the Context-for-Ui error, verify ForgeGUI still receives its root Ui plus the same context, and preserve source hash and UNAPPROVED labeling. These tests **do not** compile Rust.

No PCC registry, asset definitions, original image bytes, scene files, save data, semantic/draft plan logic, simulation, or Macroquad production code changes. Candidate workspace remains isolated and the PCC remains the sole operations authority. All C4 predecessor files other than the Rust main source remain byte-identical, except this new test and handoff.

## What to do on Windows

Drop this **unextracted C5 cumulative ZIP alone** at Havenwild root on the `experimental` lane. The existing PCC should apply it. Run the Full Quality Gate, then Run & Play → Bevy candidate: run isolated preview. An isolated `cargo check` is also registered in Build & Verify. If a *new* compiler error appears, provide the next console output/debug bundle; do not claim this as a fully fixed candidate until `cargo check`, launch and GPU review pass.

The previous log reports `[UNCERTIFIED] Candidate Cargo.lock absent`; the first run resolved 615 packages. This is a separate reproducibility issue, not E0308. Keep the candidate's currently ignored Cargo.lock intact for investigation; do not introduce a fabricated lockfile in this patch. A future verified lockfile must come from successful Cargo resolution and be checked in deliberately through the PCC. Candidate Bevy 0.19.0 and ForgeGUI Git revisions remain unchanged.

## Certification boundary

Confirmed here: exact edited Rust callsite, original 40-file cumulative predecessor content, structural/static tests, Python tests, and patch byte hashes. Unverified here: Rust compilation, Windows GPU execution, in-game parity, PIE, ElizaWy role certification, and new Full PCC gate. The existing user-reported C4 GREEN remains the checkpoint and this patch is an unverified candidate awaiting actual PCC test.
