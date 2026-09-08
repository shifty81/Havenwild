#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[5]
errors: list[str] = []


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        errors.append(f"missing {rel}")
        return ""
    return path.read_text(encoding="utf-8")


def load_json(rel: str) -> dict:
    text = read(rel)
    if not text:
        return {}
    try:
        return json.loads(text)
    except Exception as exc:
        errors.append(f"invalid json {rel}: {exc}")
        return {}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


asset_intake = read("crates/haven_assets/src/asset_intake.rs")
user_registry = read("crates/haven_assets/src/user_asset_registry.rs")
asset_palette = read("crates/haven_assets/src/asset_palette.rs")
atlas_render = read("apps/haven_editor_native/src/app/atlas_render.rs")
intake_panel = read("apps/haven_editor_native/src/app/asset_intake_panel.rs")
app_mod = read("apps/haven_editor_native/src/app/mod.rs")
dock = read("apps/haven_editor_native/src/app/object_inspector.rs")
scene_edit = read("crates/haven_editor/src/scene_edit.rs")
build_ps1 = read("tools/build/Build.ps1")
build_sh = read("tools/build/Build.sh")
validation_registry = read("crates/haven_editor/src/validation_registry.rs")
contract = load_json("content/editor/assets/asset_intake_atlas_authoring_contract_v0_1.json")
catalog = load_json("content/assets/intake/asset_intake_catalog_v0_1.json")
manifest = load_json("assets/generated/user_imports/havenwild_intake_atlas_v0_1.json")
read("docs/editor/ASSET_INTAKE_ATLAS_AUTHORING_PASS53.md")

checks = [
    ("pub struct AssetIntakeCatalog", asset_intake, "asset intake catalog model is missing"),
    ("pub fn scan_inbox", asset_intake, "asset inbox scanner is missing"),
    ("pub enum AssetLicenseStatus", asset_intake, "license status gate is missing"),
    ("pub fn promotion_issues", asset_intake, "promotion validation is missing"),
    ("license acceptance must be explicitly confirmed", asset_intake, "explicit license acceptance is not enforced"),
    ("pub struct UserAssetRegistry", user_registry, "generated user asset registry is missing"),
    ("binding_for_tile", user_registry, "dynamic tile binding is missing"),
    ("binding_for_object", user_registry, "dynamic object binding is missing"),
    ("authored_object_footprint", user_registry, "authored footprint resolution is missing"),
    ("load_user_asset_registry_default", asset_palette, "palette does not consume promoted bindings"),
    ("AssetProvenance::ProjectOwnedImport", asset_palette, "promoted asset provenance is missing"),
    ("self.user_registry.binding_for_tile", atlas_render, "tile renderer does not consume promoted atlas bindings"),
    ("self.user_registry.binding_for_object", atlas_render, "object renderer does not consume promoted atlas bindings"),
    ("binding.pivot", atlas_render, "promoted object pivots are not used"),
    ("reload_user_assets", atlas_render, "atlas texture reload is missing"),
    ("pub(crate) fn draw_asset_intake", intake_panel, "native Intake tab drawing is missing"),
    ("pub(crate) fn handle_asset_intake_click", intake_panel, "native Intake tab interaction is missing"),
    ("Scan Inbox", intake_panel, "inbox scan control is missing"),
    ("Bake + Reload", intake_panel, "bake and reload control is missing"),
    ("poll_asset_hot_reload", intake_panel, "manifest timestamp polling is missing"),
    ("reload_asset_outputs_if_requested", intake_panel, "async hot reload path is missing"),
    ("SceneDockTab::Intake", dock, "Intake dock tab is not wired"),
    ("mod asset_intake_panel;", app_mod, "asset intake panel module is not registered"),
    ("app.reload_asset_outputs_if_requested().await", app_mod, "editor run loop does not reload promoted assets"),
    ("authored_object_footprint(object)", scene_edit, "new object placement ignores authored footprints"),
    ("asset-bake", build_ps1, "Windows build entry point omits asset-bake"),
    ("asset-bake", build_sh, "shell build entry point omits asset-bake"),
    ("asset_intake_atlas_authoring", validation_registry, "editor validation registry omits Pass 53"),
]
for needle, text, message in checks:
    if needle not in text:
        errors.append(message)

for rel, text in [
    ("asset_intake.rs", asset_intake),
    ("user_asset_registry.rs", user_registry),
    ("asset_intake_panel.rs", intake_panel),
    ("atlas_render.rs", atlas_render),
]:
    if len(text.splitlines()) > 750:
        errors.append(f"{rel} exceeds the 750-line module ceiling")

if contract:
    if contract.get("pass") != "53":
        errors.append("Pass 53 contract has the wrong pass number")
    promotion = contract.get("promotionGate", {})
    if promotion.get("explicitAcceptanceRequired") is not True:
        errors.append("contract does not require explicit license acceptance")
    if promotion.get("approvedTargetMustBeUnique") is not True:
        errors.append("contract does not require unique promoted targets")
    editor = contract.get("editor", {})
    for key in ("dedicatedIntakeTab", "scanInbox", "validateRecipe", "bakeAndReload", "manifestTimestampHotReload", "paletteRefreshAfterReload"):
        if editor.get(key) is not True:
            errors.append(f"contract does not require editor.{key}")

recipes = catalog.get("recipes", []) if isinstance(catalog, dict) else []
if catalog.get("schema") != "havenwild.asset_intake_catalog.v0_1":
    errors.append("asset intake catalog schema mismatch")
if catalog.get("atlasOutput") != "assets/generated/user_imports/havenwild_intake_atlas_v0_1.png":
    errors.append("asset intake atlas output mismatch")
if not recipes:
    errors.append("asset intake catalog has no proof recipe")
seen_ids: set[str] = set()
seen_targets: set[str] = set()
for recipe in recipes:
    stable_id = recipe.get("stableId", "")
    if stable_id in seen_ids:
        errors.append(f"duplicate intake stableId {stable_id}")
    seen_ids.add(stable_id)
    source = str(recipe.get("sourcePath", "")).replace("\\", "/")
    if source.startswith("assets/reference_quarantine/"):
        errors.append(f"quarantined source entered intake catalog: {source}")
    if not source.startswith(("assets/source/intake/", "assets/source/original/")):
        errors.append(f"intake source outside approved roots: {source}")
    if not (ROOT / source).is_file():
        errors.append(f"missing intake source {source}")
    if recipe.get("promotionState") == "approved":
        target = recipe.get("target", {})
        target_id = f"{target.get('kind')}/{target.get('code')}"
        if target_id in seen_targets:
            errors.append(f"duplicate approved target {target_id}")
        seen_targets.add(target_id)
        license_record = recipe.get("license", {})
        if license_record.get("status") not in {"project_owned", "cc0", "cc_by", "third_party_approved"}:
            errors.append(f"approved recipe {stable_id} has blocked license")
        if license_record.get("accepted") is not True:
            errors.append(f"approved recipe {stable_id} lacks explicit acceptance")

entries = manifest.get("entries", []) if isinstance(manifest, dict) else []
if manifest.get("schema") != "havenwild.user_asset_atlas.v0_1":
    errors.append("generated user atlas manifest schema mismatch")
if manifest.get("generatedBy") != "tools/automation/assets/Bake-AssetIntakeAtlasV66.py":
    errors.append("user atlas manifest generator mismatch")
if len(entries) != sum(recipe.get("promotionState") == "approved" for recipe in recipes):
    errors.append("generated user atlas entry count does not match approved recipes")
if not any(entry.get("target") == {"kind": "object", "code": "cave_entrance"} for entry in entries):
    errors.append("project-owned cave entrance proof binding is missing")

atlas_path = ROOT / "assets/generated/user_imports/havenwild_intake_atlas_v0_1.png"
if not atlas_path.is_file():
    errors.append("generated user asset atlas PNG is missing")
else:
    try:
        with Image.open(atlas_path) as image:
            width, height = image.size
        for entry in entries:
            x, y, w, h = entry.get("rect", [0, 0, 0, 0])
            if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > width or y + h > height:
                errors.append(f"atlas rect exceeds PNG bounds: {entry.get('stableId')}")
    except Exception as exc:
        errors.append(f"invalid user atlas PNG: {exc}")

if not errors and atlas_path.is_file():
    before_png = digest(atlas_path)
    manifest_path = ROOT / "assets/generated/user_imports/havenwild_intake_atlas_v0_1.json"
    before_manifest = digest(manifest_path)
    completed = subprocess.run(
        [sys.executable, str(ROOT / "tools/automation/assets/Bake-AssetIntakeAtlasV66.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if completed.returncode:
        errors.append(f"deterministic asset bake failed: {completed.stderr.strip()}")
    elif digest(atlas_path) != before_png or digest(manifest_path) != before_manifest:
        errors.append("asset intake bake is not deterministic")

if errors:
    print("Asset intake and atlas authoring validation failed:")
    for error in errors:
        print(" -", error)
    raise SystemExit(1)

print("Asset intake and atlas authoring validation passed.")
