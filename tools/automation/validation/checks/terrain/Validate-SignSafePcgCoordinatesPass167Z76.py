from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[5]
surface = (
    (ROOT / "crates/haven_world/src/continuous_surface.rs").read_text(encoding="utf-8")
    + "\n"
    + (ROOT / "crates/haven_world/src/continuous_surface_tests.rs").read_text(encoding="utf-8")
)
island = (
    (ROOT / "crates/haven_world/src/island_pcg.rs").read_text(encoding="utf-8")
    + "\n"
    + (ROOT / "crates/haven_world/src/island_pcg_tests.rs").read_text(encoding="utf-8")
)
authority = json.loads(
    (ROOT / "content/worldgen/open_world_surface_runtime_authority_v0_2.json").read_text(
        encoding="utf-8"
    )
)

errors = []
for marker in [
    "encode_pcg_grid_token",
    "token.strip_prefix('n')",
    "token.strip_prefix('p')",
    '"pcg_havenwild_mainland_n2_7"',
    "pcg_surface_scene_ids_keep_legacy_nonnegative_coordinates_loadable",
]:
    if marker not in surface:
        errors.append(f"missing continuous-surface sign-safe marker: {marker}")


if "parse_surface_grid_token" not in surface and "parse_pcg_grid_token" not in surface:
    errors.append("missing continuous-surface sign-safe marker: shared grid-token parser")

if "crate::continuous_surface::pcg_surface_scene_id" not in island:
    errors.append("PCG generation does not use the shared sign-safe partition identity builder")
if "generated_scene_ids_encode_negative_partition_coordinates_losslessly" not in island:
    errors.append("missing negative-coordinate generation regression test")
if '"pcg_{}_{}_{}"' not in surface:
    errors.append("PCG scene ID format is no longer explicit in the shared authority")

rules = authority.get("runtimeRules", {})
if rules.get("pcgSignedCoordinateEncoding") != "negative_n_prefix_nonnegative_decimal":
    errors.append("open-world authority does not declare the sign-safe PCG token encoding")
if rules.get("projectSceneIdNormalizationMustNotEraseCoordinateSign") is not True:
    errors.append("open-world authority does not prohibit sign loss through scene-ID normalization")

if errors:
    raise SystemExit("Z76 validation failed:\n- " + "\n- ".join(errors))
print("Pass167Z76 sign-safe PCG partition coordinates validated")
