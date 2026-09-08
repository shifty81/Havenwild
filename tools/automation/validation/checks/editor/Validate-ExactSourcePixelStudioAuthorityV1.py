#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
DOCUMENT = ROOT / "crates/haven_pixel/src/document.rs"
PERSISTENCE = ROOT / "crates/haven_pixel/src/persistence.rs"
BRIDGE = ROOT / "apps/haven_editor_native/src/app/world_asset_pixel_bridge.rs"
CONTEXT = ROOT / "apps/haven_editor_native/src/app/scene_asset_context.rs"
RENDER = ROOT / "apps/haven_editor_native/src/app/pixel_studio_render.rs"
INPUT = ROOT / "apps/haven_editor_native/src/app/pixel_studio_input.rs"


def need(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(f"FAIL W44A exact-source Pixel Studio authority: {message}")


def text(path: Path) -> str:
    need(path.is_file(), f"missing {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8-sig")


def main() -> int:
    document = text(DOCUMENT)
    persistence = text(PERSISTENCE)
    bridge = text(BRIDGE)
    context = text(CONTEXT)
    render = text(RENDER)
    input_rs = text(INPUT)

    # The metadata contract must remain backward-compatible while carrying the
    # immutable upstream rectangle separately from the cropped derived document.
    need("pub source_region: Option<PixelSelection>" in document, "metadata lacks source_region provenance")
    before = document.split("pub source_region: Option<PixelSelection>", 1)[0]
    need("#[serde(default)]" in before[-180:], "source_region is not backward-compatible via serde(default)")

    # Exact-source loading must crop the upstream image and keep ordinary Save
    # on the Havenwild-derived output lane, never overwrite licensed source art.
    need("pub fn load_source_region(" in persistence, "exact-region loader missing")
    need("image::imageops::crop_imm(" in persistence, "exact-region loader/reset does not crop source")
    need("source region is empty" in persistence, "empty source rectangle is not rejected")
    need("exceeds" in persistence and "upstream.width()" in persistence, "source bounds are not validated")
    need('output_path: format!("assets/source/original/pixel_studio/{stem}.png")' in persistence,
         "derived Pixel Studio output path was removed")
    need("metadata.source_region = Some(source_region);" in persistence, "source rectangle provenance is not retained")
    need("pub fn reset_to_source_region(" in persistence, "reset/rebase-to-source operation missing")

    # Scene context must distinguish an object from the ground tile under it.
    need("pub object_id: Option<ObjectId>" in context, "scene context menu cannot retain selected object identity")
    need("SceneAuthoringLayer::Objects" in bridge, "right-click does not hit-test the object layer")
    need("resolve_scene_object_asset" in bridge, "published object exact-source resolver missing")
    need("resolve_persistent_ref" in bridge, "object source does not follow persistent PublishedWorldAsset ref")
    need("for_legacy_object" in bridge, "legacy ObjectKind compatibility adapter missing")
    need("definition.provenance.source_path" in bridge, "object exact source path is not provenance-backed")
    need("definition.provenance.source_rect" in bridge, "object exact source rectangle is not provenance-backed")
    need("has no reviewed exact source" in bridge, "missing/rejected objects do not fail closed")

    # Both terrain and objects converge on one cropped-document opening path.
    need("fn open_resolved_world_asset_source(" in bridge, "shared terrain/object exact-source opener missing")
    need("PixelDocument::load_source_region(" in bridge, "world bridge does not use cropped exact-source documents")
    need("PixelDocument::load(&source_path" not in bridge, "world bridge still opens the complete source atlas/sheet")
    need("self.pixel_studio.show_atlas_grid = false" in bridge, "exact-source document still presents atlas grid")
    need("self.pixel_studio.frame_document" in bridge, "exact-source document is not framed on open")

    # Exact-source editing is derived/non-destructive. Keep Save, Publish, and
    # Reset as separate actions so Reset never steals the publishing workflow.
    need('"Save Working Copy"' in render, "derived Save action missing")
    need('"Publish Slice Draft"' in render, "publish action was replaced by reset")
    need('"Reset Source"' in render, "reset-to-upstream action missing")
    need("pixel_fit_visual_rect(rect)" in render and "exact_source_context" in render,
         "Reset Source is not contextual to exact-source documents")
    need("Runtime binding is unchanged until Publish Slice Draft -> approve -> Bake + Reload." in render,
         "Save Working Copy misleadingly implies an unpublished derived edit is live")
    world_save = bridge.split("pub(crate) fn save_world_asset_pixels_and_return", 1)
    need(len(world_save) == 2, "world-asset save/return bridge missing")
    need("asset_hot_reload_requested = true" not in world_save[1][:2200],
         "derived exact-source Save incorrectly requests runtime hot reload before publish/approval")
    need("Runtime binding is unchanged until Publish Slice Draft -> approve -> Bake + Reload." in world_save[1][:2600],
         "world-asset save/return status does not disclose the publish/approval gate")
    publish_block = input_rs.split("if pixel_publish_rect(rect).contains(mouse)", 1)
    need(len(publish_block) == 2 and "self.publish_pixel_document();" in publish_block[1][:220],
         "Publish Slice Draft no longer publishes")
    fit_block = input_rs.split("if pixel_fit_visual_rect(rect).contains(mouse)", 1)
    need(len(fit_block) == 2 and ".reset_to_source_region(repo_root_dir())" in fit_block[1][:1800],
         "Reset Source control does not call reset_to_source_region")

    print("PASS W44A exact-source Pixel Studio authority")
    print("- terrain and PublishedWorldAsset objects open cropped exact source regions")
    print("- licensed/upstream source remains provenance; ordinary Save targets derived Havenwild output")
    print("- missing/rejected object bindings fail closed instead of opening generated atlases")
    print("- Save Working Copy, Publish Slice Draft, and Reset Source remain distinct workflows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
