# Native Editor Stamp Provider Test Contract — Pass167Z92

## Purpose

Close the final `haven_assets` workspace-test failure after Pass167Z91 without removing the promoted structural-cliff provider or restoring the obsolete pond-only stamp policy.

## Correct production policy

The default registry is a licensed, semantically promoted, multi-provider registry. Each entry retains provider-qualified identity, source provenance, category, footprint, license, and runtime/editor eligibility.

Current required providers include:

- `havenwild_objects` for ElizaWy-backed expandable ponds and Havenwild object catalogs.
- `oga_lpc_cliffs` for the approved grass-top structural-cliff, ramp, ladder, cave, and bridge catalog.

Future providers must be added through the same asset-pack, license, semantic-promotion, and validation gates. Tests should verify required provider contracts rather than assume every stamp shares one source sheet.

## Acceptance

- Full validation, formatting, Cargo check, and strict Clippy remain green from the Pass167Z91 Windows report.
- The repaired `haven_assets` test requires both the ElizaWy pond and OGA LPC cliff ladder.
- Pack IDs and source-sheet identities are asserted.
- Windows path separators are normalized.
- No lint suppression or production behavior change is introduced.

## Next editor lane

With the build gate closed, development returns to the continuous Alderreach World Editor: one global authoring canvas for terrain, elevation, structural cliffs, roads, objects, structures, lots, and zones, with storage partitions visible only as optional diagnostics.
