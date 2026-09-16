# Havenwild Experimental HW-46 through HW-55

Base: `experimental` commit `66b1bc4c37ae382093031f5683a4ec3b4ddaceb3` (`HW-EXPERIMENTAL-TOOLING-36-45-PCC-V2`).

This cumulative block continues the Havenwild-specific Ember mirror without introducing an Ember repository dependency.

## Passes

- **HW-46 — PCC v2 lifecycle certification.** Startup, restart, patch evidence and gate-blocking rules receive an explicit lifecycle contract and validator.
- **HW-47 — ForgePY/PCC provider parity.** The project-native provider reports the live registry vocabulary and exposes the same stable gate/lane/status operations used by standalone PCC.
- **HW-48 — Shared editor action authority.** `haven_authoring::EditorActionId` becomes the command identity. The native editor registry becomes a label/menu adapter rather than a second enum authority.
- **HW-49 — Jobs, progress, Problems and logs contract.** Headless operation records distinguish queued/running/terminal jobs and structured Problems entries.
- **HW-50 — Editor Core service boundary.** Commands, documents, selection, transactions, content, assets, jobs, Problems, runtime bridge, persistence and studio registry receive one explicit owner each.
- **HW-51 — Project Files / Content Browser authority.** Project files and asset surfaces share stable content references and one query contract instead of parallel path-only models.
- **HW-52 — Inspector / selection / document context.** Active document, open documents, dirty state, selection and inspector target become one serializable context contract.
- **HW-53 — Integrated Studio registry.** Atlas Mapper is formally an integrated Havenwild Editor Studio; its old launcher is retained only as a thin adapter during migration.
- **HW-54 — PIE/runtime bridge contract.** Play, Play From Here, Restart and Stop are explicit requests; Play From Here requires an explicit scene and world location and may not silently degrade to Play.
- **HW-55 — Experimental Editor Architecture certification.** A single validator verifies the new source and data contracts before Full Gate proceeds.

## Architectural result

```text
Havenwild Editor native host
        |
        +-- labels / chrome / canvas rendering
        |
        v
haven_authoring headless Editor Core
        +-- stable action IDs
        +-- documents + selection + inspector context
        +-- transactions / undo-redo
        +-- project-content identity
        +-- jobs + Problems
        +-- Studio registry
        +-- PIE request contract
        |
        +--> haven_assets / haven_save / existing development bridge
```

The intent is consolidation, not duplication. Existing mature runtime/editor systems stay in place and migrate behind these seams incrementally.

## R1 root-handoff correction

The first HW-46→55 gate attempt exposed a workflow ambiguity rather than a source regression: a `Havenwild_CumulativeSourceRollup_*.zip` was placed in the live repository root. The update intake correctly ignored it because a source rollup has no `PATCH_MANIFEST.json`; the strict root-cleanliness audit then failed before build/test.

R1 adds `PccRootHandoffClassifier.ps1`. PCC v2 now classifies known cumulative/full source rollups and source snapshots before update discovery and before gate root audit. Valid handoffs are moved to `artifacts/packages/received/<timestamp>`; handoffs with malformed/mismatched supplied SHA-256 sidecars are moved to `artifacts/packages/quarantine/<timestamp>`. Only manifest/update transports are allowed to mutate repository source.

This preserves the strict clean-root contract while making the workflow tolerant of a common drag/drop mistake.
