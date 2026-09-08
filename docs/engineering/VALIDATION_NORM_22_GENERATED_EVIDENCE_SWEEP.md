# VALIDATION-NORM-22 — Generated Evidence Sweep

This pass generalizes VALIDATION-NORM-21 instead of fixing generated preview files one-by-one.

Converted direct generated-evidence `require_file(...)` calls: **1**.

Current-source validation:
- source/runtime/editor contracts remain mandatory;
- generated previews, screenshots, audit renders and artifact outputs are evidence;
- recognized generated evidence is validated when present but may be absent;
- non-generated source references continue to fail closed.

Explicit historical/release certification remains free to regenerate and require deterministic
visual evidence.

Remaining suspicious direct generated/render/preview `require_file` calls after the sweep:
[
  {
    "line": 500,
    "text": "require_file(entry[\"lpcMappedPreview\"])"
  },
  {
    "line": 501,
    "text": "require_file(entry[\"comparisonPreview\"])"
  },
  {
    "line": 535,
    "text": "terrain_render = require_file("
  },
  {
    "line": 702,
    "text": "terrain_render = require_file("
  },
  {
    "line": 794,
    "text": "bridge_render = require_file("
  }
]
