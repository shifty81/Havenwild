# Pass 155B1 — V122 Validator Compatibility Hotfix

Pass 155B moved mapped-terrain transition traversal onto the retained visible-cell worklist. The runtime capability remained present, but the historical V122 validator still required obsolete pre-worklist source spellings using local `x`, `y`, `px`, `py`, and `cached` variables.

This hotfix updates V122 to validate the active retained-cell implementation:

- mapped-terrain coverage check uses `cell.x` and `cell.y`;
- mapped atlas availability uses the current `Option::is_some()` guard;
- transition overlay submission is validated by its active call and retained transition payload;
- atlas padding safeguard remains required.

No runtime terrain, V7 topology, material, water, world-generation, save, or gameplay behavior changed.
