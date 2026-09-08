#!/usr/bin/env python3
"""Validate the LPC same-family promotion plan."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
POLICY = ROOT / "content/assets/lpc/lpc_environment_topology_policy_v0_1.json"
PLAN = ROOT / "content/assets/lpc/lpc_same_family_promotion_plan_v0_1.json"

REQUIRED_ROLES = {
    "center_fill",
    "isolated",
    "end_north",
    "end_east",
    "end_south",
    "end_west",
    "straight_north_south",
    "straight_east_west",
    "corner_north_east",
    "corner_south_east",
    "corner_south_west",
    "corner_north_west",
    "tee_north_east_south",
    "tee_east_south_west",
    "tee_south_west_north",
    "tee_west_north_east",
    "cross",
    "mixed_role_deferred",
}

ROAD_PATH_BRIDGE = {"road", "stone_path", "mountain_path", "bridge"}


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require_text(path: str, needles: list[str]) -> None:
    payload = read(path)
    missing = [needle for needle in needles if needle not in payload]
    if missing:
        raise SystemExit(f"V118: {path} missing {missing}")


def main() -> int:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    plan = json.loads(PLAN.read_text(encoding="utf-8"))

    if plan.get("neighborModel") != "eight_neighbor":
        raise SystemExit("V118: same-family promotion plan must use eight_neighbor")
    if plan.get("version") != "0.1.0":
        raise SystemExit("V118: expected same-family plan version 0.1.0")

    safety = " ".join(plan.get("runtimeSafety", [])).lower()
    for needle in [
        "one complete replacement role",
        "do not layer complete replacement cells",
        "planning and validation pass only",
    ]:
        if needle not in safety:
            raise SystemExit(f"V118: runtime safety is missing '{needle}'")

    roles = set(plan["sameFamilyRoleRequirements"]["roles"])
    missing_roles = sorted(REQUIRED_ROLES - roles)
    if missing_roles:
        raise SystemExit(f"V118: role requirements missing {missing_roles}")

    policy_same_family = set(policy["rules"]["same_family_assembly"]["families"])
    groups = plan["promotionGroups"]
    group_members = [
        tile_kind
        for group in groups
        for tile_kind in group["tileKinds"]
    ]
    if set(group_members) != policy_same_family or len(group_members) != len(set(group_members)):
        missing = sorted(policy_same_family - set(group_members))
        extra = sorted(set(group_members) - policy_same_family)
        duplicates = sorted({item for item in group_members if group_members.count(item) > 1})
        raise SystemExit(
            f"V118: same-family coverage mismatch missing={missing} extra={extra} duplicates={duplicates}"
        )

    road_group = next((group for group in groups if group["id"] == "road_path_bridge"), None)
    if road_group is None:
        raise SystemExit("V118: missing road_path_bridge promotion group")
    if set(road_group["tileKinds"]) != ROAD_PATH_BRIDGE:
        raise SystemExit("V118: road_path_bridge must cover road, stone_path, mountain_path, and bridge")
    if road_group.get("priority") != min(group["priority"] for group in groups):
        raise SystemExit("V118: road_path_bridge must be the first same-family promotion priority")
    if road_group.get("status") != "planned_mapping_required":
        raise SystemExit("V118: road_path_bridge must remain mapping-required until sources are verified")

    exposure = " ".join(str(value) for value in plan["editorExposure"].values()).lower()
    for needle in ["mapping required", "not direct paint buttons", "object or stamp"]:
        if needle not in exposure:
            raise SystemExit(f"V118: editor exposure policy missing '{needle}'")

    require_text(
        "tools/automation/validation/checks/terrain/Validate-LpcMixedCornerTopologyV116.py",
        ["mixed edge-plus-diagonal contacts do not layer pure inner-corner art"],
    )
    require_text(
        "docs/PASS105_LPC_ENVIRONMENT_TOPOLOGY_POLICY_20260713.md",
        ["Pass 105 adds that contract without changing tile rendering behavior"],
    )
    require_text(
        "docs/PASS106_LPC_SAME_FAMILY_PROMOTION_PLAN_20260713.md",
        [
            "Pass 106 does not change renderer behavior",
            "Roads, paths, and bridges are the first same-family promotion target",
            "No layered complete replacement roles",
        ],
    )

    print("V118 OK: same-family LPC promotion plan covers roads, caves, interiors, cliffs, and bridges safely")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
