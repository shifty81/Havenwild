# Pass 134 LPC Tuple Promotion Plan

Pass 134 turns the Pass 133 coverage audit into a prioritized promotion queue.

The tuple renderer now has safe terrain-v7 ownership for all audited material
pairs, but many rows still fall back to pure fills. Those fallback rows are
valid enough to prevent stale legacy atlas artifacts, but they are not final
visual polish. This pass ranks them so exact tuple art can be authored in the
right order:

- Production water and shore edges first.
- Deep/shallow water transitions second.
- Production land edges third.
- Advanced or rare material combinations after the overworld basics.

Generated outputs:

- `content/assets/lpc/lpc_tuple_promotion_plan_v0_1.json`
- `docs/assets/LPC_TUPLE_PROMOTION_PLAN_PASS134.md`
- `docs/assets/previews/havenwild_lpc_tuple_promotion_plan_pass134.png`
