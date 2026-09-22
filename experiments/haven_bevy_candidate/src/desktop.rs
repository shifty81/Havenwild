//! Experimental desktop shelf for EXISTING Havenwild candidate tools only.
//! No fake Pixel/Animation/Logic/Sound tool launchers and no second dock owner.
use bevy_egui::egui;
use forge_gui_shell::ForgeShellState;

/// Names and IDs refer only to actual CandidateContent::surface implementations.
/// ForgeGUI retains all panel ownership, docking, and visibility.
pub(crate) const TASK_TOOLS: &[(&str, &str)] = &[
    ("source_library", "Sources"),
    ("source_preview", "Atlas"),
    ("inspector", "Inspector"),
    ("world_semantics", "Semantics"),
    ("scene_evidence", "Scene Evidence"),
    ("infrastructure", "Evidence"),
    ("activity", "Activity"),
];

fn toggle_tool(shell: &mut ForgeShellState, id: &str) -> bool {
    if !TASK_TOOLS.iter().any(|(candidate, _)| *candidate == id) {
        return false; // Never allow the permanent Game Canvas to be minimized.
    }
    if shell.surface_visible(id) {
        shell.hide_surface(id)
    } else {
        shell.open_surface(id)
    }
}

/// One shelf inside the SAME primary window; embedded floating panels are not
/// extra OS windows. Future studios must register real resource-backed tools.
pub(crate) fn show_task_shelf(root: &mut egui::Ui, shell: &mut ForgeShellState) {
    egui::Panel::bottom("havenwild.candidate.task_shelf")
        .resizable(false)
        .show(root, |ui| {
            ui.horizontal_wrapped(|ui| {
                ui.strong("Game Canvas");
                ui.separator();
                ui.label("Tools:");
                for &(id, label) in TASK_TOOLS {
                    let visible = shell.surface_visible(id);
                    if ui.selectable_label(visible, label)
                        .on_hover_text(if visible { "Hide tool (state retained)" } else { "Show tool" })
                        .clicked()
                    {
                        toggle_tool(shell, id);
                    }
                }
                ui.separator();
                ui.label("Experimental · mapping and PIE not certified");
            });
        });
}

#[cfg(test)]
mod tests {
    use super::*;
    use forge_gui_chrome::{ModularSurfaceState, ShellProfile, SurfaceDock};

    #[test]
    fn task_shelf_only_toggles_registered_tools_and_preserves_center() {
        let mut shell = ForgeShellState::new(ShellProfile::Standard, vec![
            ModularSurfaceState::new("world_draft", "Game Canvas", SurfaceDock::Center),
            ModularSurfaceState::new("source_preview", "Atlas", SurfaceDock::Floating),
        ]);
        assert!(!toggle_tool(&mut shell, "world_draft"));
        assert!(shell.surface_visible("world_draft"));
        assert!(toggle_tool(&mut shell, "source_preview"));
        assert!(!shell.surface_visible("source_preview"));
        assert!(toggle_tool(&mut shell, "source_preview"));
        assert!(shell.surface_visible("source_preview"));
        assert_eq!(shell.surface("source_preview").unwrap().dock, SurfaceDock::Floating);
        assert!(!toggle_tool(&mut shell, "pixel_studio"));
    }
}
