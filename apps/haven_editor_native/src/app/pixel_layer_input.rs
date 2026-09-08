use super::*;

impl EditorApp {
    pub(crate) fn handle_pixel_layer_rename_input(&mut self) -> bool {
        let Some(buffer) = self.pixel_studio.layer_rename_buffer.as_mut() else {
            return false;
        };
        while let Some(character) = get_char_pressed() {
            if !character.is_control() && buffer.chars().count() < 48 {
                buffer.push(character);
            }
        }
        if is_key_pressed(KeyCode::Backspace) {
            buffer.pop();
        }
        if is_key_pressed(KeyCode::Escape) {
            self.pixel_studio.layer_rename_buffer = None;
            self.status_message = "Layer rename cancelled".to_string();
            return true;
        }
        if is_key_pressed(KeyCode::Enter) {
            let name = self
                .pixel_studio
                .layer_rename_buffer
                .take()
                .unwrap_or_default();
            if let Some(document) = self.pixel_studio.document.as_mut() {
                if document.rename_active_layer(name) {
                    self.status_message = "Layer renamed".to_string();
                }
            }
            return true;
        }
        true
    }

}
