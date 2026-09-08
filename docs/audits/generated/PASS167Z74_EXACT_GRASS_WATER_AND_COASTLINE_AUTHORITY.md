# Pass 167Z74 — Exact Grass/Water and Coastline Authority

- Exact F3/native-editor terrain cells are authoritative and survive editor close, save, reload, and paint-delta replay.
- Replaying world-paint deltas no longer runs the generated coastline lifecycle afterward.
- Existing-save generation migrations perform targeted tile/object migrations only; they do not rebuild coastlines.
- Generated coastline cleanup remains active only for fresh worldgen packs, starter generation, explicit regeneration, Coast mode, and Hydrology mode.
- A grass cell painted beside water remains grass. It is never silently converted to V7 sand.
- Direct grass/water contacts that lack a certified V7 tuple remain visible and are reported as unsupported until the user invokes Coast/Hydrology or the V7 mapping is expanded.
- No terrain pixels or tilesheets are generated or modified.
