# B13R1 — Reproducible ElizaWy source-hash diagnosis

## Evidence and decision

After a clean pinned-cache checkout and complete 64,365-file physical mirror, the
Windows B13 audit reported 64,326 raw matches and 39 mismatches. The historical
index contains **exactly 40 non-image records**: 35 `Credits.txt` files, three
JSON files, `README.md`, and `.gitignore`. The proximity of 39 and 40 makes
checkout LF/CRLF transformation a plausible hypothesis, **not a verified cause**.
The original B13 auditor did not publish mismatch filenames or distinguish a
line-ending difference from altered artwork or metadata.

## This correction

- Keeps the pinned ElizaWy commit, historical index, B12 policy, original
  assets, legacy validators, editor/client, and PCC unchanged.
- Hashes all indexed source files on explicit `--full-index` as before.
- Recognizes an LF/CRLF equivalent file **only for** `.txt`, `.json`, `.md`,
  and `.gitignore`, below 8 MiB, with no NUL byte, and **only when both the
  historical SHA-256 and historical byte count match transformed bytes**.
  No other whitespace, encoding, case, compression, image, or semantic
  normalization is permitted. Original files are never rewritten.
- Separates `hashedFiles` (raw-exact) from `lineEndingEquivalent` (strictly
  proven normalization) and `verifiedFiles` (sum). Reports paths, expected and
  actual sizes and SHA-256 for each proven equivalence. Still blocks any
  unproven mismatch, missing file, unexpected file, invalid PNG, altered
  authority, or missing source provenance. Adds up to 50 mismatch and
  missing-file examples to the JSON report.
- Leaves one historically unreadable zero-byte PNG quarantined; does not grant
  per-asset, legal, visual, tile, world, or runtime approval.

## Windows verification

From Havenwild root (Experimental lane), run the quick 40-document diagnostic
first, then only run the complete hash audit once the text findings are clear:

```powershell
py -3 tools/automation/assets/Diagnose-ElizaWyTextHashB13R1.py --root . --report WORKSPACE/generated/lpc/elizawy_b13r1_text_diagnostic.json
py -3 tools/automation/assets/Certify-ElizaWySourceB13.py --root . --full-index --report WORKSPACE/generated/lpc/elizawy_b13_report.json
notepad WORKSPACE/generated/lpc/elizawy_b13_report.json
```

The fast diagnostic never scans artwork or grants source certification; inspect its
`findings` if it still reports a non-line-ending difference. Do not rerun the
full 64,365-file hash check until those findings are understood.

Expected only if the LF/CRLF hypothesis is correct: `verifiedFiles: 64365`,
`missingIndexed: 0`, `mismatchedIndexed: 0`, `unexpectedFiles: 0`, and
`lineEndingEquivalent: 39`. Do **not** invent, force, or assume that output:
any remaining mismatch remains a BLOCKER and is named in `mismatchExamples`.
Keep the two mount backups until the real source audit passes.

B13R1 repairs source-certification evidence only. Do not enable ElizaWy
production cutover on a green build alone; mapping, attribution review, source
image quarantine, visual parity, traversal, and per-tile approval remain ahead.
