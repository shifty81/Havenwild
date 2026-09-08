from pathlib import Path

root = Path(__file__).resolve().parents[5]
draw = (root / "crates/haven_game/src/client_character_frontend_draw.rs").read_text(encoding="utf-8")
frontend = (root / "crates/haven_game/src/client_frontend.rs").read_text(encoding="utf-8")
required_draw = [
    "pub(crate) struct CreatorLayout",
    "pub(crate) fn creator_layout()",
    "draw_section_panel",
    "appearance_panel",
    "clothing_panel",
    "actions_y",
    "Color::from_rgba(177, 130, 72, 255)",
]
required_frontend = [
    'draw_section_panel(layout.identity_panel, "IDENTITY")',
    'draw_section_panel(layout.appearance_panel, "APPEARANCE")',
    'draw_section_panel(layout.clothing_panel, "CLOTHING & ACCESSORIES")',
    'draw_button(creator_cancel_rect(), "BACK", false)',
    'draw_button(creator_confirm_rect(), "SAVE CHARACTER", true)',
]
missing = [token for token in required_draw if token not in draw]
missing += [token for token in required_frontend if token not in frontend]
legacy = [
    'Rect::new(screen_width() * 0.5, 218.0 + row as f32 * 39.0',
    'Rect::new(screen_width() * 0.5 - 190.0, 760.0',
    'form.y + 688.0',
]
found_legacy = [token for token in legacy if token in draw or token in frontend]
if missing or found_legacy:
    if missing:
        print("Pass 149J23 FAILED - missing responsive creator layout contracts:")
        for token in missing:
            print(f"  - {token}")
    if found_legacy:
        print("Pass 149J23 FAILED - legacy fixed/overlapping creator coordinates remain:")
        for token in found_legacy:
            print(f"  - {token}")
    raise SystemExit(1)
print("Pass 149J23 responsive categorized Havenwild character creator layout validated")
