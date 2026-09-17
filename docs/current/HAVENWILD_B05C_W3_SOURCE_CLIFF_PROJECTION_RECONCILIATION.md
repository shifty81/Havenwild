# B05C — Reconcile B05B cliff projection with W3 source-authority (2026-09-17)

## Evidence, not an assumed visual fix

The user's QG-20260917-154002-b5316bdf debug bundle confirms both original ElizaWy source and V7 source passed SHA-256 verification. The expected derived cliff overlay was absent. The checked-in builder reproduced SHA-256 `8a009b52c74792714c955a7fbc44d964a2110d8d1b835118b62c9f44ae28a7d4`; B05B enforced the superseded W109G SHA-256 `25b7a65f892b897d7664e8d68091661a159a41715617a18bccd185f173d9608d`. The quality gate failed before Rust compilation.

The later active `content/worldgen/authored_terrain_provider_authority_v0_1.json` has `revision=167Z109W3-*`, requiring `strip_semantic_ground` **only in the derived overlay**, original rock geometry unchanged, and V7 as plateau/receiver owner. The existing `Build-ElizaWyCliffRuntimeOverlayPass167Z109D.py` implements this W3 policy; the previous B05B guard erroneously required the superseded W109G output hash and contract.

## Changes

- Align active projection and three cross-referencing content contracts to the measured W3 derivative hash. Preserve source-asset hashes and original builder; neither raw image is edited or bundled.
- Require active W3 provider metadata and W3 builder source policy before rebuilding. Keep temporary-build, exact hash/dimensions, and atomic replacement protections. Any different source/builder/PNG still fails closed.
- Mark the superseded W109D/G projection validator as historical while W3 is active, retaining its old assertions when W3 is absent. This prevents contradictory old-vs-new visual rules from becoming coequal authorities.
- Add guarded recovery regression tests for stale pass, missing provider, old builder policy, corrupt existing outputs, original source hash failures, and atomic publication.

## Expected checkpoint

Drop this incremental ZIP into Havenwild root on top of applied B05B, run PCC Full Quality Gate. Expected build log: both original sources VERIFIED, generated W3 projection RECOVERED or VERIFIED. On GREEN, launch editor and actual game and inspect cliffs in the same coordinates. **Do not count GREEN as a cliff visual pass.** This only restores the required source-derived texture. If cliffs remain missing, inspect structural host and renderer binding; water lag and partition seams are separate B05D/E work.

No source artwork is included, no SHA lock on either original source is relaxed, and no generated placeholder pixels are introduced.
