# Pass 133 LPC Tuple Coverage Audit

Pass 133 adds a generated audit board for the terrain-v7 tuple renderer.

The audit enumerates the 16 binary corner patterns for every current terrain
material pair and classifies each pattern as:

- `exact`: authored terrain-v7 tuple art exists.
- `fallback`: terrain-v7 owns the cell through a pure-material fallback, so old
  atlas overlays stay suppressed.
- `missing`: no exact tuple or safe terrain-v7 fallback exists.

This is the bridge between screenshot-driven fixes and finishing the rest of
the terrain in bulk. The renderer can already keep missing water/land tuples
inside the terrain-v7 path; this board shows which fallback-heavy pairs should
be promoted into exact authored tuple art next. Production pairs remain listed
separately in the JSON so we can prioritize common overworld work before rare
or advanced material combinations.

Generated outputs:

- `content/assets/lpc/lpc_tuple_coverage_audit_v0_1.json`
- `docs/assets/LPC_TUPLE_COVERAGE_AUDIT_PASS133.md`
- `docs/assets/previews/havenwild_lpc_tuple_coverage_pass133.png`
