# Havenwild V7 Water-Tier Presentation Audit — Pass167Z69

## Build evidence

Pass167Z68 passed source validation, formatting, Cargo check, and strict Clippy. The test suite then reported three failures in `haven_assets`: two tests expected direct V7 shallow/deep tuples and one palette test still counted retired Wet Sand.

## Atlas evidence

The source-pure normalized V7 manifest contains 4,035 entries. Audit of its corner signatures found:

- authored `Water`/`Water_Deep` combinations;
- authored `Water`/`Water_Shallows_Dirt` combinations;
- authored `Water`/`Water_Shallows_Sand` combinations;
- no direct `Water_Deep`/`Water_Shallows_Dirt` combination;
- no direct `Water_Deep`/`Water_Shallows_Sand` combination.

Therefore the correct source-backed presentation is three-tier, not a fabricated direct shallow/deep edge.

## Resolution

The semantic map keeps the original depth and water-domain IDs. Only presentation material resolution derives a medium V7 `Water` rim on deep cells beside same-domain shallows. Exact V7 tuple overlays then handle both tier boundaries.

Wet Sand remains a compatibility alias only and is excluded from normal authoring counts.

## Risk review

- No atlas pixels changed.
- No generated image was added.
- No ElizaWy source was referenced.
- No save migration was added.
- No collision or swimming rule changed.
- Ocean and freshwater raw identities remain intact.
