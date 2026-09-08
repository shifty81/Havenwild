# Pass 149C — Continuous Overworld Runtime and Shared Canvas Framework

## Implemented now

- Native-editor canvas zoom expanded from 25–300% to 1–3200%.
- Pixel Studio zoom expanded to 6.25–7200%.
- Cursor-centered wheel zoom remains active.
- Ctrl+Plus, Ctrl+Minus, and Ctrl+0 are normalized across spatial canvases.
- World, scene, and pixel canvases use top/left rulers, adaptive ticks, cursor crosshairs, and coordinate readouts.
- Inspector width increased and paired controls now size from available width.
- `Overworld Layout` is renamed `World Surface`; exterior slots are presented as streaming chunks rather than gameplay scenes.
- A continuous-surface manifest binds the legacy authored exterior maps into chunk coordinates.
- Exterior-to-exterior transfers are treated as hidden chunk-streaming compatibility operations. Interior/cave/special-area transitions remain explicit.

## Important boundary

The compatibility bridge removes exterior scene semantics from the user-facing workflow, but the current runtime still stores the four inherited authored exterior maps in the legacy scene registry internally. The next world-streaming pass must replace that internal bridge with a true multi-chunk active window and shared world-space player coordinates.

## Next implementation

1. Load a 3×3 active chunk window and 5×5 metadata/preload ring.
2. Move player position to canonical global tile/pixel coordinates.
3. Persist authored overrides per chunk.
4. Generate unassigned chunks on demand.
5. Retain scene documents only for interiors and special instances.
