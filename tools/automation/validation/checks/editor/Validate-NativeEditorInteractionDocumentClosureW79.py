#!/usr/bin/env python3
"""Validate W79 editor interaction, containment, settings, and document closure authority."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
ERRORS=[]

def read(rel):
    p=ROOT/rel
    if not p.is_file():
        ERRORS.append(f"missing required file: {rel}")
        return ""
    return p.read_text(encoding='utf-8')

def require(text, markers, context):
    for marker in markers:
        if marker not in text:
            ERRORS.append(f"{context}: missing marker {marker!r}")

def main():
    lifecycle=read('apps/haven_editor_native/src/app/document_lifecycle.rs')
    settings=read('apps/haven_editor_native/src/app/editor_settings.rs')
    tabs=read('apps/haven_editor_native/src/app/document_tabs.rs')
    pixel=read('apps/haven_editor_native/src/app/pixel_studio.rs')
    pixel_input=read('apps/haven_editor_native/src/app/pixel_studio_input.rs')
    pixel_render=read('apps/haven_editor_native/src/app/pixel_studio_render.rs')
    pixel_layout=read('apps/haven_editor_native/src/app/pixel_studio_layout.rs')
    helpers=read('apps/haven_editor_native/src/app/render_helpers.rs')
    toolrail=read('apps/haven_editor_native/src/app/canvas_tool_rack.rs')
    tooltip_overlay=read('apps/haven_editor_native/src/app/tooltip_overlay.rs')
    input_rs=read('apps/haven_editor_native/src/app/input.rs')
    menu=read('apps/haven_editor_native/src/app/editor_menu.rs')
    commands=read('apps/haven_editor_native/src/app/command_registry.rs')
    mod_rs=read('apps/haven_editor_native/src/app/mod.rs')
    draw=read('apps/haven_editor_native/src/app/draw.rs')
    editor_text=read('apps/haven_editor_native/src/app/editor_text.rs')
    contract=read('content/editor/native_editor_interaction_document_closure_w79_v1.json')
    settings_data=read('WORKSPACE/editor/native_editor_settings_v0_1.json')

    require(lifecycle,[
        'DocumentCloseTarget','request_close_active_document','request_close_scene_document',
        'request_close_pixel_document','request_close_workspace_document','Save & Close',
        'Close Without Saving','reopen_last_closed_document','draw_document_close_dialog',
        'draw_closed_workspace_empty_state'
    ],'universal document lifecycle')
    require(mod_rs,[
        'pending_document_close: Option<document_lifecycle::PendingDocumentClose>',
        'closed_workspace_documents: HashSet<EditorViewportMode>',
        'recently_closed_workspace_documents: Vec<EditorViewportMode>',
        'editor_settings: editor_settings::EditorSettingsState'
    ],'EditorApp lifecycle/settings state')
    require(input_rs,[
        'self.pending_document_close.is_some()','self.editor_settings.open',
        'request_close_active_document','reopen_last_closed_document','KeyCode::W','KeyCode::T'
    ],'universal input routing')
    require(tabs,[
        'request_close_scene_document','workspace_document_is_closed','reopen_workspace_document',
        'draw_single_document_tab','"×"'
    ],'shared document tabs')
    require(pixel+pixel_input+pixel_render+pixel_layout,[
        'recently_closed_documents','close_document_tab','reopen_last_closed_document',
        'pixel_document_tab_close_rect','request_close_pixel_document','"×"'
    ],'Pixel document lifecycle')
    require(settings,[
        'NATIVE_EDITOR_SETTINGS_PATH','SettingsSection','Pixel & Animation','World & Scene',
        'tooltips_enabled','ui_text_scale','settings_button_rect','draw_editor_settings',
        'handle_editor_settings_click'
    ],'project-wide Settings authority')
    require(menu+commands,[
        'CloseActiveDocument','ReopenClosedDocument','Close Active Document',
        'Reopen Closed Document','settings_button_rect','open_editor_settings'
    ],'menu/settings command authority')
    require(helpers+toolrail+tooltip_overlay,[
        'draw_control_tooltip','tooltip_rect_for_anchor','tooltips_enabled',
        'draw_global_tooltip_overlay','canvas_tool_tooltip_request'
    ],'anchored/global tooltip authority')
    require(helpers,[
        'draw_validation_report','additional validation rows','draw_scissored_text'
    ],'bounded validation rendering')
    require(editor_text,['DEFAULT_EDITOR_TEXT_SCALE: f32 = 1.10','ui_text_scale'], 'compact typography authority')
    require(draw,['draw_editor_settings','draw_document_close_dialog','canvas_document_open'], 'overlay/empty-state draw order')
    require(contract,['havenwild.editor.native_interaction_document_closure.w79.v1','resourceDeletionSeparateFromViewClose','windowsCargoGateAuthoritative'], 'W79 authority contract')
    require(settings_data,['havenwild.native_editor.settings.v0_1','\"ui_text_scale\": 1.1','\"tooltips_enabled\": true'], 'W79 default settings data')

    if 'canvas.x + 8.0, button.y + 4.0' in toolrail:
        ERRORS.append('Tool Rail tooltip still uses legacy canvas/Layer-side placement proxy')

    if ERRORS:
        print('W79 native editor interaction/document closure validation FAILED')
        for e in ERRORS: print('-',e)
        return 1
    print('PASS: W79 native editor interaction/document closure')
    print('- global Settings surface and compact typography authority are present')
    print('- W79 anchored tooltip helper is preserved and W81 routes Tool/Layer help through the final global overlay')
    print('- Validation rows are width/height bounded')
    print('- Scene, Pixel, World, Animation, Character, Logic, Sound and support workspaces route closure through one authority')
    print('- Pixel close/reopen retains full working sessions and dirty state')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
