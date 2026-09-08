from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[5]
def text(path: str) -> str:
    target = ROOT / path
    assert target.is_file(), f"missing {path}"
    return target.read_text(encoding="utf-8")

contract = json.loads(text("content/editor/pixel_editor/operational_pixel_studio_v149g.json"))
assert contract["schema"] == "havenwild.editor.pixel_studio_operational.v149g"
assert len(contract["documentKinds"]) == 8
assert contract["creation"]["sidecarExtension"] == "hhasset.json"

creation = text("crates/haven_pixel/src/document_creation.rs")
for token in [
    "PixelDocumentKind",
    "NewPixelDocumentSpec",
    "create_document",
    "Tilesheet",
    "CharacterLayer",
    "maxPixels" if False else "16_777_216",
]:
    assert token in creation, f"missing creation token {token}"

state = text("apps/haven_editor_native/src/app/pixel_studio.rs")
assert "new_dialog" in state
assert "create_from_dialog" in state
assert "scan_pixel_library" in state

input_rs = text("apps/haven_editor_native/src/app/pixel_studio_input.rs")
for token in ["KeyCode::N", "KeyCode::O", "KeyCode::S", "handle_new_pixel_dialog_input"]:
    assert token in input_rs, f"missing input token {token}"

render = text("apps/haven_editor_native/src/app/pixel_studio_render.rs")
assert '"New Asset"' in render

registry = text("crates/haven_editor/src/validation_registry.rs")
assert "operational_pixel_studio_v149g.json" in registry

print("Pass 149G operational Pixel Studio contract validated")
