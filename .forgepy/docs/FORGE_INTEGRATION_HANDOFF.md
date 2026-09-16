# Forge / Cortex integration handoff — U5

Treat repository-local ForgePY as the project's normalized execution/certification provider.

## Preferred machine connection

Start `ForgePY.cmd serve-jsonl` (`forgepy.universal.jsonl.v2`). Supported queries include:

- `status`
- `operations`
- `capabilities`
- `identity`
- `patches`
- `history`
- `scan`
- `snapshot`
- `run`

`{"op":"snapshot"}` is the preferred initial/project-refresh request because it returns status, operations, patch inbox, recent Git history and the automatic build plan together. Stdout remains strict JSONL; human run output is sent to stderr.

## Semantic invocation

Cortex/Ember should request semantic operations (`build`, `test`, `run`, `full`, or explicit normalized keys), not hardcode Cargo/CMake/npm commands. Read operation `_provider`, `_component`, `cwd`, and the project `discovery` block when displaying ownership/evidence.

## Repository onboarding

U5 can scan an unfamiliar repository and synthesize a build plan without requiring a hand-written contract. Read `buildPlan.components`, `buildPlan.defaults`, `buildPlan.warnings` and `buildPlan.unresolved`. Do not interpret unresolved project families as buildable until a project adapter/contract declares deterministic commands.

## Provider authority

Provider precedence remains Internal PCC → root contract → ForgePY adapter → automatic discovery. Mature projects should map their authoritative PCC into `forge.project.v1`; generated operations only fill gaps.

## Responsibility boundary

Cortex supplies reasoning/orchestration. Ember supplies the landing page/tool panels/Forge Console. ForgePY executes normalized local project operations and returns structured evidence. Vault/global Git hosting/full-drive organization remain separate cores.
