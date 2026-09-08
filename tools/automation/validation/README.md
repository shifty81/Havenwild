# Havenwild validation

The validation system is deliberately split by purpose so normal development is not blocked by historical certification machinery.

## Profiles

- `build` / `quick` — **2 lightweight gates** used by normal builds:
  1. repository/development layout;
  2. Havenwild-owned JSON parsing and ownership scope.
- `source` — **10 current-authority gates** used by the **Validate current source** menu command. The set is intentionally bounded: newer normalization authority replaces the previous pass-specific source gate rather than accumulating historical gates.
- `framework` — **4 framework-only gates** for validator self-tests and quality checks.
- `full` — explicit certification profile containing the registered historical/subsystem checks plus Cargo format/check/Clippy/tests. It is never run implicitly by `Build all`.

## Entry points

- `validation_runner.py` — authoritative profile runner.
- `validate_development_layout.py` — repository and tooling layout.
- `validate_architecture.py` — Rust module size and architecture policy.
- `validate_project_content.py` — Havenwild-owned JSON scope and parsing.
- `validate_content_integrity.py` — current gameplay/asset contracts.
- `validate_terrain_topology_v167z5.py` — explicit terrain evidence certification.

Compatibility wrappers remain for older commands, but they do not add gates to normal builds.

## Historical checks

Pass-specific validators remain under `checks/<domain>/` for diagnosis, source archaeology, and explicit certification. Their presence does not activate them during normal builds.
