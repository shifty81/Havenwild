# B18 — source-native ground contact evidence (not production approval)

## Inputs and authority

B18 consumes B13's fully reproduced pinned-source certification, B14's ElizaWy-only candidate routing, B15's source-cell inventory, B16's original source candidates and board, and B17's semantic proposals. It rehashes the same seven original source PNG sheets. It does not redefine terrain grammar from V7, call external tools, rescan 64,365 files, touch the PCC, change save data, or activate a renderer.

The user-supplied B17 `lpc.zip` contains the generated proposal report and review board; cross-checking the B16 board SHA-256 confirms their provenance. The review board is static: seeing a preview is not an approval transaction.

## Proven information versus unresolved behavior

B18 reconstructs 42 original-sheet placements belonging to ten proposals. For each multi-cell region, row-major source cell IDs and coordinates establish 229 **internal contiguous grid pairs**. These are evidence of the original authored rectangle only, **not proof of visually seamless edges or permission to paint one edge/corner independently**. Its 314 external boundary slots remain unresolved. Across ten candidate groups, the 55 unordered candidate-pair categories (including self-pairs) start unsupported until separately evidenced; real terrain contact rules must eventually include direction, season, orientation, underlay and water/traversal semantics. The 25 single-cell placements have unreviewed repeatability.

A 3×3 grass patch is an overlay whose underlying material still needs source evidence; the grass pool and 4×3 shore strip must preserve their complete source layouts. The teal/dark water appearances cannot establish water depth. Tilled soil cannot establish wet/dry gameplay state. Ice-shallows cannot establish walkable collision. Internal arrangement never authorizes generic autotiling across unrelated assemblies.

## Run and expected result

From the Havenwild root, after applying the patch through the Experimental PCC:

```powershell
py -3 tools/automation/assets/Build-ElizaWyGroundContactReviewB18.py --root .
start WORKSPACE/generated/lpc/elizawy_ground_contact_review_b18.html
py -3 tools/automation/validation/checks/assets/Test-ElizaWyGroundContactReviewB18.py
```

Expected status `SOURCE_INTERNAL_CONTACTS_CATALOGUED_EXTERNAL_REVIEW_REQUIRED`, 42 source placements, 229 internal grid pairs, 314 external slots, 55 unapproved candidate-pair categories, zero blockers, **zero approved topology rules, zero published runtime bindings**. The generated report lists each exact source cell and original internal/external boundary; the HTML shows complete source placements and review queue.

B19 must review true neighboring authored components and produce explicit directional/seasonal/underlay contact recipes with visual evidence. Do not switch the editor/client until the runtime bindings, gameplay tests, license tracking and editor-client parity are separately certified. Preserve all legacy save references and other providers as inactive reference assets.
