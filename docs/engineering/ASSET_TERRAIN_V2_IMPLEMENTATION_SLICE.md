# Asset/Terrain V2 implementation slice

This crate is deliberately dependency-free and contains the shared primitives that will be consumed
by the production world/runtime/editor during cutover.

It does not replace the existing runtime merely by existing. The next migration step wires these
types into the existing shared runtime and development-session/PIE bridge, then deletes displaced
V1 authority only after parity evidence is GREEN.

Core rule:

`semantic state + local connections/context -> exact authored recipe -> resolved resource/draw plan`

Surface terrain and structural cliffs both autotile through connection keys. Cliff connectivity is
derived from the authoritative heightfield/contour graph rather than neighboring artwork.
