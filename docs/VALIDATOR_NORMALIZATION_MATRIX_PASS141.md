# Validator Normalization Matrix — Pass 141

| Lifecycle | Meaning | Blocks source/full | How to run |
|---|---|---:|---|
| `active` | Current authoritative project contract | Yes | `validation_runner.py source` |
| `legacy-reference` | Historical pass assertion, generated-preview check, or superseded implementation detail | No | `validation_runner.py legacy` |
| `retired` | Preserved only for audit history; not executable by default | No | Explicit manifest reactivation only |

The legacy profile intentionally reports historical assumptions separately. A legacy failure must be promoted into an active replacement validator before it can block current development.

Pass-number scripts V109 and newer are initially classified as active because they represent the normalized terrain/runtime lane through Pass 141. Earlier checks remain inventoried as legacy-reference unless covered by architecture, content, or world foundation validation.
