use super::*;

impl Game {
    pub(super) fn adjust_selected_transition(&mut self) {
        let (x, y) = self.selected_cell;
        let mut status = None;
        let editing = is_key_pressed(KeyCode::Up)
            || is_key_pressed(KeyCode::Down)
            || is_key_pressed(KeyCode::Right)
            || is_key_pressed(KeyCode::Left)
            || is_key_pressed(KeyCode::Comma)
            || is_key_pressed(KeyCode::Period)
            || is_key_pressed(KeyCode::Slash)
            || is_key_pressed(KeyCode::Semicolon);
        if editing && self.world.active().transition_at(x, y).is_some() {
            self.push_undo_snapshot();
        }
        if let Some(transition) = self.world.active_mut().transition_at_mut(x, y) {
            if is_key_pressed(KeyCode::Up) {
                transition.h += 1;
            }
            if is_key_pressed(KeyCode::Down) {
                transition.h = (transition.h - 1).max(1);
            }
            if is_key_pressed(KeyCode::Right) {
                transition.w += 1;
            }
            if is_key_pressed(KeyCode::Left) {
                transition.w = (transition.w - 1).max(1);
            }
            if is_key_pressed(KeyCode::Comma) {
                transition.spawn_x = (transition.spawn_x - 1).max(0);
            }
            if is_key_pressed(KeyCode::Period) {
                transition.spawn_x = (transition.spawn_x + 1).min(MAP_W as i32 - 1);
            }
            if is_key_pressed(KeyCode::Slash) {
                transition.spawn_y = (transition.spawn_y + 1).min(MAP_H as i32 - 1);
            }
            if is_key_pressed(KeyCode::Semicolon) {
                transition.spawn_y = (transition.spawn_y - 1).max(0);
            }
            status = Some(format!(
                "Transition {} size {}x{} spawn {},{}",
                transition.label,
                transition.w,
                transition.h,
                transition.spawn_x,
                transition.spawn_y
            ));
        }
        if let Some(status) = status {
            self.status_message = status;
        }
    }

    pub(super) fn edit_selected_transition(&mut self, edit: TransitionEdit) {
        let len = self.world.active().transitions.len();
        if len == 0 {
            self.status_message = "Active scene has no transitions".to_string();
            return;
        }
        self.selected_transition_index = self.selected_transition_index.min(len - 1);
        self.push_undo_snapshot();
        let selected = self.selected_transition_index;
        match edit {
            TransitionEdit::CycleTarget => {
                let current_target = self.world.active().transitions[selected].target.clone();
                let current = SceneId::ALL
                    .iter()
                    .position(|id| current_target.legacy_scene_id() == Some(*id))
                    .unwrap_or(0);
                let next = SceneId::ALL[(current + 1) % SceneId::ALL.len()];
                let (spawn_x, spawn_y) = self
                    .world
                    .scene(next)
                    .map(|scene| (scene.spawn_x, scene.spawn_y))
                    .unwrap_or((23, 13));
                let transition = &mut self.world.active_mut().transitions[selected];
                transition.target = next.into();
                transition.spawn_x = spawn_x;
                transition.spawn_y = spawn_y;
                transition.label = format!("To {}", next.label());
                self.selected_transition_target = (current + 1) % SceneId::ALL.len();
                self.status_message = format!("Transition now targets {}", next.label());
            }
            TransitionEdit::Grow => {
                let transition = &mut self.world.active_mut().transitions[selected];
                transition.w = (transition.w + 1).min(MAP_W as i32 - transition.x);
                transition.h = (transition.h + 1).min(MAP_H as i32 - transition.y);
                self.status_message = format!("Transition size {}x{}", transition.w, transition.h);
            }
            TransitionEdit::Shrink => {
                let transition = &mut self.world.active_mut().transitions[selected];
                transition.w = (transition.w - 1).max(1);
                transition.h = (transition.h - 1).max(1);
                self.status_message = format!("Transition size {}x{}", transition.w, transition.h);
            }
            TransitionEdit::SetDestination => {
                let (x, y) = self.selected_cell;
                let transition = &mut self.world.active_mut().transitions[selected];
                transition.spawn_x = x.clamp(0, MAP_W as i32 - 1);
                transition.spawn_y = y.clamp(0, MAP_H as i32 - 1);
                self.status_message = format!(
                    "Transition destination {},{}",
                    transition.spawn_x, transition.spawn_y
                );
            }
            TransitionEdit::Delete => {
                self.world.active_mut().transitions.remove(selected);
                self.selected_transition_index = self.selected_transition_index.saturating_sub(1);
                self.status_message = "Deleted selected transition".to_string();
            }
        }
    }
}
