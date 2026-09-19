# B48R21 — one workflow, equal inspection panes, PCC feedback

## Baseline and purpose

Cumulative overlay based on B48R20. The user reports the previous pass GREEN and pushed, but B48R21 has **not** been certified on Windows. No old level-one restrictions or alternate mapper introduced. This is still the original `apps/haven_atlas_mapper_lite` tool.

## Actual change

- Existing left source atlas and right scene get equal space at startup, with a draggable middle divider constrained to 40–60%. The misleading decorative LIB/MAP/COL/LAY/PUB rail has been removed.
- Sheet browser takes 44% of left height rather than ~62%, giving the actual tile atlas a larger preview. Zoom/pan and ON/OFF controls remain.
- Inspector is closed by default, opens with Details or `I`, floats over the right pane, and blocks painting underneath. It is no longer a permanent third column.
- Top row contains project actions; second row is the single ordered action sequence: Draft → Learn → Stage missing cells → Audit → Review → Handoff. Commands formerly duplicated in inspector have been removed from that panel. Save master remains explicit and reopens on startup when an actual saved project exists.
- Stage missing cells is **not** recipe-driven reroll. The tool does not contain a certified automatically assembled Summer master. No approved map/collision/worldgen publication is implied.
- PCC root patch intake emits timestamps and progress before long extraction, then counters during hash validation, installation and post-apply verification; on actual success it prints archive, receipt and log location. Transactional rollback/fail-closed verification are unchanged.

## Windows acceptance sequence

1. Verify B48R20 is actually installed and GREEN in local PCC. Put only B48R21 cumulative ZIP in root; do not apply earlier cumulative ZIPs again. Approve startup intake.
2. Confirm progress is visible immediately and at regular verified file counts, followed by `[PASS] PATCH APPLIED AND VERIFIED` plus receipt/log paths. Confirm archive moved into applied; if no success receipt, inspect `logs/updates` and ledger, never assume success from menu return alone.
3. Run PCC Full Quality Gate; capture result. Open mapper. At 1600×940, left and right pane widths should match initially; drag divider left/right and verify they stay near 40–60% and neither pane paints during dragging.
4. Activate original Summer terrain/cliff/water sheets. Verify enlarged source atlas; select a tile and correct it on the right, save and reopen. Toggle Details and ensure editing does not penetrate overlay.
5. Draft → edit → save → Learn → Stage missing → Audit → Review → Handoff. Confirm unchanged user edits, truthful draft/learned markers, unreviewed export, original-source evidence and no false green checks.

## Pending work, not disguised as finished

Actual approved editable Summer demo, source-role topology compiler, procedural seed reroll, deterministic correction promotion, complete furniture composites and cliff-water recipes, collision/nav/engine parity, native Windows interactive GUI test and Full Quality Gate for this patch. ForgeGUI may be a future window/chrome host but should not be imported wholesale into this existing Macroquad workbench without auditing dependencies and avoiding a second mapping authority.
