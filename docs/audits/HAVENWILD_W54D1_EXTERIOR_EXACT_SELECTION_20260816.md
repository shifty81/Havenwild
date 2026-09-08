# Havenwild W54D1 — Exterior Exact Selection Lock

Date: 2026-08-16  
Baseline: Pass167Z109W54C  
Pass type: evidence selection only / no Rust / no runtime binding

## Purpose

W54D1 advances the W54C exterior evidence queue without moving the mandatory W54B/W54C Windows compile boundary. It records exact human-reviewed source rectangles that are already visually unambiguous, while leaving unresolved side/back/corner and complex-roof semantics fail-closed.

## Exact selections locked

From `Structure/Walls/Siding, Plain.png`, the first two reviewed palettes expose an authored 5-column x 3-row frontage grammar. W54D1 locks six 1x3 vertical source strips:

- cream light: left / repeat / right;
- blue light: left / repeat / right.

Each strip is exactly 32x96 pixels and is composed from three vertically adjacent 32x32 source cells. These are **south/frontage selections only**.

## Explicit non-claims

W54D1 does not claim that these strips are north, east or west wall facings. It does not rotate or mirror them. It does not assign wall corner semantics. It does not break `Hipped Shingle Roof A` into guessed hip/valley cells.

Whole-building LPC sheets remain reference-only.

## Runtime boundary

No changes are made to:

- Rust source;
- `PublishedWorldAssetRegistry` runtime packs;
- the W54A Estate cottage recipe;
- Estate generation;
- BuildingInstance geometry;
- render/collision behavior.

The next runtime publication gate remains after the Windows build plus the local W54C evidence bundle.
