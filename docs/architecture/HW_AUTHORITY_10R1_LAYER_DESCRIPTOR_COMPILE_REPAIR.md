# HW-AUTHORITY-10R1 — Layer Descriptor Compile Repair

The AUTH-10 layer contract added `generated`, `derived`, `diagnostic`, and
`writable` to `CanvasLayerDescriptor`. Three older struct literals were missed:
two production literals in `canvas_layers.rs` and one test helper in
`pixel_layer_rail.rs`.

This repair completes those initializers without changing the AUTH-10
architecture. Source-reference rows are read-only/derived, generated source
references are marked generated, Character rows inherit writability from their
locked-order state, and the Pixel test helper uses `!locked` for writability.
