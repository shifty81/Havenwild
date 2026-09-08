# Havenwild Pass 96D — Strict Clippy Option Extraction Hotfix

Pass 96C reached Cargo successfully. Formatting and workspace checking passed;
strict Clippy then requested idiomatic `?` extraction for two optional fields in
`MaterialMaskBuilder::finish`.

Pass 96D applies those two mechanical changes without altering transition
behavior. V109 now verifies both the earlier match-arm separator and these
strict-Clippy-compatible Option extractions.

Extract this complete source rollup over the repository and run:

```bat
tools/build/Build.cmd all
```
