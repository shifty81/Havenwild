# Havenwild Pass 96 — LPC Edge-Signature Seam Conformance

Pass 96 continues from the Pass 95 summer runtime semantic promotion. It does
not remap the pinned LPC source or replace the ordered terrain families.

## Corrected failure

The raw LPC roles are authored as pieces of larger compositions. After a role
was cropped and normalized, a fringe pixel could remain on a cardinal edge
that the runtime mask considered internal. When two owner-material cells were
adjacent, that source fringe appeared as a thin retained grass, sand, or bank
border.

The normalized baker now treats the runtime topology mask as authoritative:

- an edge present in `mask4` may retain authored transition alpha;
- an edge absent from `mask4` must be alpha-clean;
- diagonal-only 2×2 inner-corner overlays may not touch cardinal edges;
- every baked entry records deterministic north/east/south/west alpha
  signatures in the atlas manifest;
- V108 rejects any atlas containing transition pixels on an internal edge.

The final composited art remains the pinned LPC artwork. This pass removes only
pixels that contradict the selected topology role; it does not recolor,
stretch, rotate, or invent transition art.

## Build

From the repository root on Windows:

```bat
tools/build/Build.cmd lpc-seams
tools/build/Build.cmd all
```

The development menu exposes the same focused operation as option 19.

## Runtime verification

Verify these shapes in both client and native editor:

1. one sand cell surrounded by grass;
2. two adjacent sand cells;
3. a 2×2 sand block;
4. L and U shapes;
5. diagonal-only contact;
6. dry-sand/wet-sand rings;
7. sand/shallow-water banks;
8. shallow/deep-water rings;
9. scene-edge continuity;
10. undo, redo, save, reload, and repaint.

Internal joins should show the base material continuously, while exterior
edges and verified concave corners retain the authored LPC transition.

## Validation

- Python syntax and Bash syntax can run without the binary asset tree.
- Full V108 atlas verification requires the normal pinned LPC dependency mount
  and generated terrain assets.
- Run `tools/build/Build.cmd all` on the Windows development machine for Cargo formatting,
  check, strict Clippy, Rust tests, validators, and packaging.
