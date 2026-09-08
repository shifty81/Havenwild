use super::*;

impl Game {
    pub(super) fn world_paint_delta_last_sequence(log: &mut GameLog, delta_path: &str) -> u64 {
        match load_world_paint_delta_document(delta_path) {
            Ok(doc) => {
                let last = doc
                    .records
                    .iter()
                    .map(|record| record.sequence)
                    .max()
                    .unwrap_or(0);
                if last > 0 {
                    log.event(&format!(
                        "World paint delta sequence restored at #{last:04}"
                    ));
                }
                last
            }
            Err(err) => {
                log.event(&format!(
                    "World paint delta sequence restore skipped: {err}"
                ));
                0
            }
        }
    }

    pub(super) fn replay_world_paint_deltas_into_world(
        world: &mut GameWorld,
        log: &mut GameLog,
        delta_path: &str,
        scene_filter: Option<SceneReference>,
        context: &str,
    ) -> String {
        match load_and_replay_world_paint_deltas(world, delta_path, scene_filter) {
            Ok(report) => {
                // Paint deltas are authored overrides. Replaying them must not run
                // the generated-coastline lifecycle afterward, because that would
                // rewrite exact grass/dirt cells beside water into beach sand.
                let status = format!("{context}: {}", report.status_line());
                log.event(&status);
                for issue in report.issues.iter().take(4) {
                    log.event(&format!("{context} issue: {}", issue.status_line()));
                }
                status
            }
            Err(err) => {
                let status = format!("{context}: paint delta replay skipped ({err})");
                log.event(&status);
                status
            }
        }
    }

    pub(super) fn replay_paint_deltas_after_world_load(&mut self, context: &str) {
        let delta_path = self.save_paths.world_paint_delta.clone();
        let status = Self::replay_world_paint_deltas_into_world(
            &mut self.world,
            &mut self.log,
            &delta_path,
            None,
            context,
        );
        self.world_paint_delta_status = status.clone();
        self.world_paint_edit_sequence =
            Self::world_paint_delta_last_sequence(&mut self.log, &delta_path);
        self.status_message = status;
        self.inspector = inspect_scene_cell(
            self.world.active(),
            self.selected_cell.0,
            self.selected_cell.1,
        );
        self.refresh_world_paint_render_bindings_for_active_scene(
            "Post-load paint render binding refresh",
        );
    }

    pub(super) fn prepare_world_paint_deltas_before_save(&mut self) {
        let delta_path = self.save_paths.world_paint_delta.clone();
        let status = Self::replay_world_paint_deltas_into_world(
            &mut self.world,
            &mut self.log,
            &delta_path,
            None,
            "Before save paint delta replay",
        );
        self.world_paint_delta_status = status;
        self.world_paint_edit_sequence =
            Self::world_paint_delta_last_sequence(&mut self.log, &delta_path);
        self.refresh_world_paint_render_bindings_for_active_scene(
            "Before-save paint render binding refresh",
        );
    }
}
