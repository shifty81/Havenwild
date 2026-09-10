# HW-ASSETS-10 — Assets Workspace Authority

Built from certified GREEN `HW-AUTHORITY-10R1` (`4803d808`). This checkpoint intentionally reuses the completed PCC compact catalog and does **not** run another broad source scan.

## Ten passes

1. **ASSET-01 Workspace** — activate `ASSETS` as a real top-level workspace while preserving the contextual right-dock Assets picker.
2. **ASSET-02 Catalog bridge** — read `artifacts/asset-intake/asset-catalog.json`; detailed SQLite remains PCC authority and is displayed as the detail-store source rather than copied into a second database.
3. **ASSET-03 Authority states** — freeze Discovered, Identified, Mapped, Validated, Certified, Deprecated, Broken.
4. **ASSET-04 Sources** — expose compact source-sheet identity, dimensions, classification, SHA lineage and assembly counts.
5. **ASSET-05 Families** — aggregate assembly candidates into reviewable source families and freeze expected semantic-role contracts for cliffs, tool visuals and humanoid animation.
6. **ASSET-06 Review** — project non-final assembly candidates into a review queue; runtime certification is never inferred from pixels automatically.
7. **ASSET-07 Provenance** — keep raw source immutable; project corrections become derived assets with lineage.
8. **ASSET-08 Usage** — reserve Where Used for dependency evidence; filename similarity is explicitly not usage authority.
9. **ASSET-09 Cliff readiness** — structural-cliff completeness requires straight/inner/outer/cap/junction/ramp/transition roles before we generate replacement art.
10. **ASSET-10 Certification** — add static quality-gate validation for workspace, catalog, family, review and no-rescan contracts.

## UI contract

Top strip: `GAME CANVAS | ASSETS | PIXEL | ANIMATION | CHARACTER | LOGIC | SOUND`.

Assets sections: `Inbox | Library | Sources | Families | Usage | Review`.

`DATA` remains a reserved canonical `WorkspaceId` but is not rendered as fake functionality.

## Source-first rule

Havenwild must prove that suitable source artwork is absent before generating replacement artwork. A missing semantic role is a review/repair condition, not permission to silently substitute unrelated pixels.

## Next build

Run the normal PCC Full Quality Gate only after all ten passes land. If GREEN, publish with Option 2. The next implementation vertical is structural cliffs/ramps using the Assets family/review authority rather than hand-authored per-cell fixes.
