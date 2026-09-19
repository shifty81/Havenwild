# Havenwild B48R28A — parallel architecture evidence / shadow comparison

**Scope:** additive, cumulative B48R26–B48R28A, rebased onto the **B48R26 GitHub GREEN** commit `48dc977d7f09805dfa9b4fd5b7aaa274e288c431` (whose parent is B48R25 `796895a5dd2aae3cbf3dcca37f73a54df94969ad`). This is not a complete source rollup, is not cumulative from B48R7, and does **not** mean the earlier packages have been installed. No existing files are overwritten or removed.

## What this actually implements

`tools/architecture/parallel_migration.py` is a *read-only* CLI with:

- `evidence-lock`: inspects Git branch, HEAD, working tree, PCC last-applied ledger / gate marker and optional pinned ForgeGUI checkout. Missing git metadata or ledger explicitly blocks evidence readiness; an archived ZIP cannot substitute for a live receipt. Neither reported source state nor the presence of a GREEN marker constitutes a new gate.
- `inventory`: hashes specific historical policy source files and reports which markers appear; every runtime call-site status stays **UNDETERMINED**. The 2026-09-17 snapshot cannot be assumed active in B48R25.
- `compare`: verifies pinned input hashes in two distinct, isolated directories and compares **already-generated** fixture outputs as exact bytes or parsed JSON. It does not run worldgen, game, Rust, a renderer or PCC. Semantic JSON equality permits serialization key-order differences but preserves array order and value types. Differences block, except explicitly pinned baseline/candidate hashes and a written reason, which yield `REQUIRES_SPECIFICATION_APPROVAL` instead of PASS. It emits only non-certifying receipts.

The tool rejects traversal paths, symlink escapes, missing assets, modified immutable inputs, duplicate paths, nested roots and receipt-writing inside source directories. The normal path only reads the source checkouts. `--out` writes optional diagnostics **outside both** source checkouts; its parent directories are created only there.

## Usage — no engine modifications

```powershell
py -3 tools\architecture\parallel_migration.py evidence-lock --root . --forge-root "C:\path\to\pinned\ForgeGUI_Core"
py -3 tools\architecture\parallel_migration.py inventory --root .
py -3 -m unittest discover -s tests\architecture -p "test_parallel_migration.py" -v
```

When **two independent isolated copies** have already generated their outputs and an authored fixture pins their identical input bytes, use:

```powershell
py -3 tools\architecture\parallel_migration.py compare --baseline "C:\baseline-copy" --candidate "C:\candidate-copy" --fixture "C:\fixtures\pond.json" --out "C:\parity-receipts\pond.json"
```

Fixture format:

```json
{
  "schema": "havenwild.parallel_parity_fixture.v1",
  "id": "summer-pond-elevation-1",
  "inputs": [{"path": "fixtures/source.png", "sha256": "<64 lowercase hex characters>"}],
  "outputs": [{"path": "results/pond.json", "comparison": "json", "policy": "preserve"}]
}
```

To document a **deliberate difference**, change `policy` to `intentional` and include `expectedBaselineSha256`, `expectedCandidateSha256`, and `rationale` (at least 20 characters). That yields **approval required**, never automatic runtime parity or permission to overwrite saves.

## Why no GUI or gameplay file changes in this pass

GitHub `experimental` records B48R26 (`48dc977d7f09805dfa9b4fd5b7aaa274e288c431`) as the GREEN commit. Its committed recovery source is byte-matched in the supplied B48R26 rollup; R27 and R28A remain uninstalled/unverified without a live PCC receipt. This package transports all predecessor *files* byte-for-byte and gives the PCC a non-disruptive comparison instrument. The ForgeGUI donor commit is pinned in the architecture contract, **not** yet injected into Havenwild Cargo or declared a compatible Rust toolchain. The current Macroquad mapper and game remain unchanged.

## Blocking next steps

1. On the user's current checkout, resolve PCC patch ledger state using the existing PCC. If the checkout is B48R26 GREEN with none of R27/R28A installed, apply **only the rebased cumulative R28A package**. Do not also apply the older, B48R25-targeted R28A ZIP or any separately bundled predecessor. Check the live PCC ledger and hashes before intake; this source rollup does not include `.git` or live PCC receipts.
2. Run real PCC Full Quality Gate after patch apply. A source-only unit test, clean ZIP hash or shadow-output comparison must never be reported as GREEN.
3. R28B: migrate `MapperProjectDocument` and undo to the shared authoring command contract **without changing serialized output**, provide golden v0_1–v0_7 round trips and test copies of user projects.
4. R28C: pin/verify ForgeGUI dependency/toolchain; build the `forge_gui_shell` consumer (library, multi-atlas, scene, right mapped brush palette, inspector, bottom PCC jobs), preserve Macroquad as rollback, exercise Windows pointer capture/resize/DPI and unsaved-project protections.
5. In parallel: migrate world boundary, +1–+30 elevation, ElizaWy source-first Vault/season policy with **implementation + validator + save compatibility** in the same certification slices. Do not promote the historical tuple inventory into certified artwork.
6. Establish a fixture corpus (summer-approved waterfall components, unresolved joints, 1-level submerged pond, finite-ocean edges, seasonal exceptions) and run the comparison harness against **real generated outputs** before changing authority.

## Actual certification state

- Package SHA/manifest and isolated Python unit tests may pass in the packaging environment.
- Windows Rust compilation, real GUI launch, live PCC Full Gate, worldgen parity, save migration, fixture visual approval and source-authority publication **NOT RUN**.
- No claim that the source rollup contains the Git or PCC receipt from September 19.
