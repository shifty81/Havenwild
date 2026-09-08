# Pass 155B4 Validator Hotfix

This cumulative overwrite-safe rollup updates two retained Pass 153 capability validators that still inspected the pre-extraction runtime frontend layout.

## Updated

- `tools/automation/validation/validate_pass153j_render_budget.py`
  - now checks `runtime_diagnostics.rs`, where HUD render-budget formatting lives after Pass 153T.
- `tools/automation/validation/validate_pass153k_frame_profile.py`
  - now checks current extracted runtime diagnostics rather than historical pass text in `runtime_draw.rs`.

No renderer, V7, terrain material, water shader, world-generation, save, or gameplay behavior changed.
