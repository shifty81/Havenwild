from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[5]

def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")

continuous = read("crates/haven_world/src/continuous_surface.rs") + "\n" + read("crates/haven_world/src/continuous_surface_tests.rs")
authority = json.loads(read("content/worldgen/surface_partition_identity_authority_v0_1.json"))
errors = []

required = [
    "parse_surface_grid_token(x)?",
    "parse_surface_grid_token(y)?",
    'ProjectSceneId::new("surface_x_n1_y_4")',
    "Some(ChunkCoord::new(-1, 4))",
    'ProjectSceneId::new("surface_x_p3_y_n2")',
    "Some(ChunkCoord::new(3, -2))",
    "scene_id_is_surface_partition",
]
for marker in required:
    if marker not in continuous:
        errors.append(f"missing continuous-surface marker: {marker}")

if "fn parse_signed_token" in continuous:
    errors.append("obsolete generated-only signed-token parser remains")

rules = authority.get("rules", {})
for key in [
    "pcgAndGeneratedParsersShareCoordinateTokenAuthority",
    "unsignedPositiveGeneratedIdsRemainLoadable",
    "negativeCoordinatesRemainLossless",
    "interiorIdsAreNeverSurfacePartitions",
    "unloadedSurfaceTargetsNeverTriggerPlayerFacingSceneTransfer",
]:
    if rules.get(key) is not True:
        errors.append(f"surface partition identity authority missing true rule: {key}")

examples = {item.get("id"): (item.get("x"), item.get("y")) for item in authority.get("examples", [])}
for scene_id, expected in {
    "surface_x_n1_y_4": (-1, 4),
    "surface_x_p3_y_n2": (3, -2),
    "pcg_havenwild_mainland_n2_7": (-2, 7),
}.items():
    if examples.get(scene_id) != expected:
        errors.append(f"authority example mismatch for {scene_id}: {examples.get(scene_id)}")

if errors:
    raise SystemExit("Z78 validation failed:\n- " + "\n- ".join(errors))
print("Pass167Z78 sign-safe surface partition identity validated")
