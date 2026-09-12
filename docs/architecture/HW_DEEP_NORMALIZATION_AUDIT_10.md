# HW-DEEP-NORMALIZATION-AUDIT-10

## Purpose

This pass records the project-wide normalization direction without discarding the
current Havenwild editor, asset, validation, PCC, or runtime-play functionality.
The current project already contains most of the correct systems; the next work
is to unify, refine, polish, and harden them.

## Current proven baseline

The last externally confirmed GREEN source authority is Git commit
`c622881ecbe29c67057a888ee3a01aaed9e20f1c`, which added the 06R3 published
cliff-ramp certification test/doc. Later local recovery patches are not treated
as proven until the internal PCC Full Gate passes on the user's machine.

## Preservation doctrine

1. Preserve first.
2. Normalize second.
3. Upgrade third.
4. Delete only after migrated replacement behavior is verified.

No current editor system should be ripped out just because it is visually rough
or split across modules. Existing working paths are the source of truth for the
next refactor lanes.

## Asset doctrine

Use assets as authored.

- Raw source sheets are immutable reference/input assets.
- Mechanical slicing and source indexing are inspection tools only.
- Runtime/editor authority begins with certified metadata and stable published IDs.
- Generated catalogs/caches are disposable and recoverable.
- Legacy tile/object aliases are compatibility adapters only.
- Validators verify contracts; they do not invent art rules, reshape maps, or
  repair visuals by mutating geography.

## Validation doctrine

Keep Validation V4 as the current authority. The reset is a tier refinement, not
a validation deletion:

- hard fail: unsafe paths, bad hashes, invalid authoritative schemas, missing
  sources for certified assets, duplicate IDs, bad production provenance,
  broken published registries, Rust build/test failures;
- warning: stale/corrupt generated caches, uncertified candidates, unused source
  sheets, legacy aliases with valid canonical targets, visual review pending;
- report only: historical pass information, coverage suggestions, future polish;
- deprecated/delete after migration: validators that enforce obsolete guesses or
  mutate terrain/water/cliffs to make art fit.

## Editor GUI doctrine

The editor keeps the existing Game Canvas, Assets, Pixel, Animation, Character,
Logic, and Sound surfaces. The missing piece is one consistent shell model:

- top global chrome always owns menus and workspace switching first;
- modals and popups own input above panels;
- dock chrome owns open/close/focus/resize before panel bodies;
- panel bodies may never trap top-level navigation;
- canvas gestures only run after GUI ownership declines the pointer;
- the polished Tool Rail/Layer Rail visual direction becomes shared editor
  chrome.

## PIE doctrine

Current Play / Play From Here / external development client launch is preserved.
The upgrade path adds explicit editor play modes:

- Edit;
- Simulate;
- Play In Game Canvas;
- Play From Here;
- Play In New Window;
- Standalone Game;
- future local multiplayer test.

The first Play In Game Canvas milestone may be a framed runtime-session surface
with explicit input capture, stop/pause/restart, runtime status, world id, scene
id, spawn, and asset/topology version reporting. Full shared embedded rendering
can follow after the state model is stable.

## Immediate pass order

1. Internal PCC root patch mode: preserve ZIP intake, support `.patch`, prompt
   before apply, archive successful transports, keep rollback.
2. Assets input recovery: top tabs and global chrome must work while Assets is
   open; Esc closes; R reloads; corrupt generated catalog cannot trap UI.
3. Asset catalog authority hardening: generated scan catalog is optional;
   published registries remain usable when it is corrupt.
4. Dock registry foundation: wrap current right/bottom docks in a general panel
   registry without changing panel behavior.
5. GUI polish normalization: move panel styling to common tokens/helpers.
6. Validation tier refinement: keep v4, add explicit tiering, demote disposable
   generated-cache drift.
7. Game Canvas PIE foundation: add explicit Play In Canvas state while keeping
   external Play.

## Acceptance for this pass

- The project contains machine-readable policies for asset authority, validation
  tiers, GUI/dock normalization, and Game Canvas PIE.
- Internal root patch intake is ready to recognize `.patch` transports while
  retaining existing ZIP manifest safety.
- Known stale failed root patch files from the prior bootstrap can be removed by
  the patch manifest so the repository can return to a clean gate path.
- No editor/runtime feature is removed.
