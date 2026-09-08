# Character Reference Images Audit - 2026-05-25

## Summary

Two loose visual reference images were added at the repository root and audited:

1. `character refrence male.png`
2. `character refrence female.png`

## Audit result

These are **visual reference sheets**, not runtime-ready game assets.

They were staged under:

```text
assets/raw/reference-packs/character-reference-sheets/
```

## Current implementation status

- The images are preserved as reference-only art inputs for future character scale, silhouette, facing, and outfit planning.
- They are not wired into the runtime/editor asset pipeline.

## Critical gaps moving forward

- The repo still needs a canonical player/NPC sprite direction and scale specification that turns reference imagery into usable production assets.
- These sheets should remain reference-only until the project defines a full character asset contract and provenance workflow.
