# 2.5D Reference Assets Audit - 2026-05-25

## Summary

The remaining root reference drop contained:

1. `Refrence images and zips/25D assets examples.zip`
2. Six loose generated reference PNGs in `Refrence images and zips/`

## Audit result

This material is **reference-only** and must stay quarantined from runtime bundles.

- The bundled audit note explicitly recommends using it only for visual grammar, tile coverage, sprite-sheet organization, animal animation needs, and icon scale.
- The extracted zip content includes mixed third-party/reference material, including LPC-derived assets and other uncertain-license sources.
- It must not be traced, copied directly, or promoted into shipped runtime content without explicit license review.

## Applied staging

- Staged under:

```text
assets/raw/reference-packs/25d-assets-examples/
```

- Only the source zip, audit manifest, audit markdown, contact sheet, and project-owned moodboard/reference images are retained in the active repo structure.

## Critical note

This pack should inform:

- 2.5D depth layering
- livestock/animal silhouette needs
- interior prop density
- terrain/autotile coverage expectations
- sprite-sheet organization

It should **not** be treated as production art input.
