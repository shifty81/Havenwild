# Pass 146B — Unified Validation Framework

## Purpose
Pass 146B turns the consolidated validator collection into one execution framework without requiring a risky all-at-once rewrite of every historical validator. Existing validator scripts execute through a process adapter while the runner owns stable IDs, dependency ordering, structured results, error codes, and unified reporting.

## Framework modules
- `context.py`: canonical project-root and path resolution.
- `result.py`: one result and issue schema.
- `registry.py`: registry validation and topological ordering.
- `generated_outputs.py`: freshness, hashing, and provenance helpers.
- `reporting.py`: JSON and Markdown report generation.

## Migration policy
New validators should import the framework directly. Existing validators remain compatible through the process adapter and can be migrated by domain over time. Validators are read-only; `Ensure-*` and `Build-*` own mutations.
