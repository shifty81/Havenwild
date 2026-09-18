# B17 — ElizaWy ground semantics: source-faithful proposals

## Evidence and decision boundary

B16's uploaded review board (`elizawy_ground_visual_review_b16.html`) is a static preview, not an editable approval record. The accompanying B16 output contains ten candidate groups and 42 exact source placements, all unapproved. Original ElizaWy sheets are available through the pinned source mount; the board's HTML references those local PNGs rather than embedding them. The user's informal visual inspection is useful, but cannot certify unseen adjacency, water depth, traversal or seasonal gameplay behavior.

B17 records **ten typed semantic proposals**, preserving every B16 source ID, rectangle, SHA-256 and season. It uses the existing B15 cell inventory and B16 report, rehashes only the seven source sheets, and produces a read-only comparison board and machine-readable result under `WORKSPACE/generated/lpc`. This is not a new asset registry or runtime resolver.

## Proposed categories and excluded inferences

- The three 1×1 seasonal source interiors propose `seasonal_top`, `seasonal_earth`, and `sand`. Winter top/earth are visually snow-covered or pale/frozen; do not assume their summer material semantics carry over unmodified. Even 1×1 source interiors need repeat/seam checks before certifying brush usage.
- The 3×3 grass patch is an **overlay assembly**; transparent source cells require an appropriate underlay. No individual edge/corner is certified for independent painting.
- The 3×3 grass-bordered pool and 4×3 shore strip are **multi-cell shoreline/water assemblies**. Inspect adjoining authored forms before assigning terrain contact rules.
- The teal and dark-blue single water cells represent **appearance only**. In particular, the dark-blue visual does not establish a gameplay deep-water label or swimming/collision contract.
- The tilled-soil 3×3 and ice-shallows 3×3 pieces are **authored assemblies**, not automatic farming/watering or walkable-ice rules.

## Validation and next pass

`py -3 tools/automation/assets/Build-ElizaWyGroundSemanticProposalsB17.py --root .`

Expected output: `SEMANTIC_PROPOSALS_READY_FOR_EXPLICIT_REVIEW`, ten role proposals, 42 original source placements, seven hash-verified source sheets, zero blockers; **zero approved semantic mappings, zero approved assemblies and zero topology rules**. Open `WORKSPACE/generated/lpc/elizawy_ground_semantic_review_b17.html` for the annotated review. Source assets and historical catalogs remain unchanged. Any changed/missing input, altered cell address, 1×1 misclassification, guessed water depth or premature approval fails closed.

B18 should establish *explicit reviewed* source-native assembly/contact rules and document unsupported combinations. It must not reinterpret B17's proposals as finalized semantic or runtime approval. Later certification must separately address legal attribution for promoted assets, water/cliff/rendering behavior, editor/client parity and save migration. No V7/Universal LPC substitution is allowed for newly authored ElizaWy content; existing legacy saves and active renderer are untouched.
