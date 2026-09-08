# Pass 158A Validator Consolidation Handoff

Pass 158A removes historical implementation-string validators from the normal build path.

The active Python validator now checks only content facts Cargo cannot establish: LPC lock metadata/checksums when mounted, atlas inventory and geometry, seasonal source topology, world preset structure, and generated-output registry integrity.

Generated outputs and the large LPC source mount are verified when present. Source-only rollups may defer those portions until the normal build generation/mount stage.

Old suite names remain accepted by the runner so existing scripts do not fail solely because a suite name changed; they all resolve to the same consolidated content-integrity gate.
