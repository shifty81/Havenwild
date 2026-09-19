# Havenwild B48R16 — cumulative standalone-mapper checkpoint

**Predecessor:** B48R15 candidate payload; installed state reported B48R9 GREEN
before the user's approved B48R15 intake triggered the PCC restart error.
**Delivery:** one cumulative overwrite source patch from the B48R7 family,
including all B48R15 payload files and this repair; no B48R10, B48R11, B48R12,
B48R14 or B48R15 separate install is required on a clean B48R9 checkout.
Do not install until root patch state and local modifications have been checked.

## Corrected in actual source

1. `tools/control/PccRestartTicket.ps1`: `$Host` reserved automatic variable
   assignment replaced with `$replacementHostScript` in the restart function.
2. Existing `apps/haven_atlas_mapper_lite/src/main.rs`: bounded undo/redo,
   source-safe history, input hit-region restrictions and top toolbar drawing
   order, full preflight for source references and placements before project
   load destroys the current session.
3. `src/scene_audit.rs`: new independent candidate structural/audit stage with
   errors for malformed records, warnings for real elevation boundaries and
   water contacts, explicit noncertifying lifecycle. GUI Audit button exports
   a JSON receipt next to a saved scene.
4. Inherited ElizaWy source registry, 2,919 original files and existing
   B48R7–B48R15 reference/mapper files retained. Original art is immutable.

## What is *not* completed

- No verified summer cliff-to-water, cliff-terminal, waterfall-mouth/outlet,
  pond corner or traversal recipe is asserted by B48R16.
- No animation editor, terrain recipe publication, finished collision/navigation
  inspector, source review approval workflow, native editor integration, full
  separate Characters.zip intake, or game worldgen +30 migration is asserted.
- Static checks, asset hashes and Python PNG replay are not Rust compilation,
  actual interactive GUI or a Windows PCC Full Quality Gate.

## Windows recovery/test procedure

1. Check PCC patch archive/log state. The user's B48R15 command already began
   application; a restart crash does not prove whether the patch was committed,
   archived or rolled back. If PCC won't launch, run the previously supplied
   *one-time* `Repair-HavenwildPccRestart-B48R16.ps1` outside project root and
   relaunch, then inspect status. Avoid manual overwrite of live binaries.
2. Keep older patch/evidence ZIPs out of Havenwild root. Put **only** the new
   B48R16 root-drop ZIP in root and approve via PCC. Do not extract it.
3. Run FULL QUALITY GATE. On failure, retain the automatically generated debug
   bundle; do not commit or push an unverified candidate.
4. Launch standalone `tools\launch\HavenwildAtlasMapperLite.cmd`. Activate
   two original summer sheets; place a tile from each; edit +0,+1,+30 and water;
   undo/redo a placement and a height brush; save and reload; run Audit; export
   Review PNG; verify original pixels using `verify_review.py`. Test malformed
   project rejection without losing unsaved edits, and a source deactivation
   after removing its pieces (undo history should be invalidated).
5. Only after the UI, Full Gate and artistic visual review pass should a
   visually approved recipe be considered for Asset Authority publication.
