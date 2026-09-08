use super::render_helpers::{draw_badge, draw_editor_widget, draw_list_row, draw_section_header};
use super::*;

const BANK_CARD_MIN_W: f32 = 220.0;
const BANK_CARD_H: f32 = 176.0;
const BANK_CARD_GAP: f32 = 12.0;

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub(crate) enum SceneBankGroup {
    WorldScenes,
    BuildingsInteriors,
    CavesDungeons,
    GeneratedSpecial,
}

impl SceneBankGroup {
    pub(crate) fn label(self) -> &'static str {
        match self {
            Self::WorldScenes => "World Scenes",
            Self::BuildingsInteriors => "Buildings / Interiors",
            Self::CavesDungeons => "Caves / Dungeons",
            Self::GeneratedSpecial => "Generated / Special",
        }
    }
}

fn scene_bank_group(scene: &haven_core::SceneMap) -> SceneBankGroup {
    let haystack = format!("{} {}", scene.id.code(), scene.name).to_ascii_lowercase();
    if haystack.contains("generated") || haystack.contains("template") || haystack.contains("special") {
        SceneBankGroup::GeneratedSpecial
    } else {
        match scene.kind {
            SceneKind::Exterior => SceneBankGroup::WorldScenes,
            SceneKind::Cave => SceneBankGroup::CavesDungeons,
            SceneKind::Interior => SceneBankGroup::BuildingsInteriors,
        }
    }
}

pub(crate) fn scene_bank_indices(world: &haven_core::GameWorld) -> Vec<usize> {
    let mut indices = world.scenes.iter().enumerate().map(|(index, _)| index).collect::<Vec<_>>();
    indices.sort_by(|left, right| {
        let left_scene = &world.scenes[*left];
        let right_scene = &world.scenes[*right];
        scene_bank_group(left_scene)
            .cmp(&scene_bank_group(right_scene))
            .then_with(|| left_scene.name.cmp(&right_scene.name))
            .then_with(|| left_scene.id.code().cmp(right_scene.id.code()))
    });
    indices
}

fn scene_bank_action_button_rect(rect: Rect, index: usize) -> Rect {
    Rect::new(rect.x, rect.y + 322.0 + index as f32 * 38.0, rect.w, 34.0)
}

fn scene_library_layout(viewport: Rect, scene_count: usize, selected_position: usize) -> (usize, usize, usize, f32) {
    let usable_w = (viewport.w - BANK_CARD_GAP * 2.0).max(BANK_CARD_MIN_W);
    let columns = ((usable_w + BANK_CARD_GAP) / (BANK_CARD_MIN_W + BANK_CARD_GAP))
        .floor()
        .max(1.0) as usize;
    let rows = ((viewport.h - BANK_CARD_GAP * 2.0) / (BANK_CARD_H + BANK_CARD_GAP))
        .floor()
        .max(1.0) as usize;
    let capacity = (columns * rows).max(1);
    let start = (selected_position / capacity) * capacity;
    let card_w = ((usable_w - BANK_CARD_GAP * (columns.saturating_sub(1)) as f32)
        / columns as f32)
        .max(1.0);
    (columns, capacity, start.min(scene_count.saturating_sub(1)), card_w)
}

fn scene_library_card_rect(viewport: Rect, visible_position: usize, columns: usize, card_w: f32) -> Rect {
    let column = visible_position % columns.max(1);
    let row = visible_position / columns.max(1);
    Rect::new(
        viewport.x + BANK_CARD_GAP + column as f32 * (card_w + BANK_CARD_GAP),
        viewport.y + BANK_CARD_GAP + row as f32 * (BANK_CARD_H + BANK_CARD_GAP),
        card_w,
        BANK_CARD_H,
    )
}

impl EditorApp {
    pub(crate) fn scene_bank_viewport_rect(&self) -> Rect {
        self.canvas_workspace_layout().viewport
    }

    pub(crate) fn draw_scene_bank_list(&self, rect: Rect) {
        let indices = scene_bank_indices(&self.model.world);
        let mut y = rect.y;
        draw_section_header(
            Rect::new(rect.x, y, rect.w, 24.0),
            "Scene Library",
            Some("world scenes • interiors • caves • generated/special"),
        );
        y += 34.0;
        for scene_index in indices.into_iter().take(14) {
            let Some(scene) = self.model.world.scenes.get(scene_index) else {
                continue;
            };
            let active = scene_index == self.selected_scene;
            let row_h = 44.0;
            draw_list_row(
                Rect::new(rect.x, y - 18.0, rect.w, row_h),
                &scene.name,
                Some(&format!("{}  •  {}", scene_bank_group(scene).label(), scene.id.code())),
                active,
            );
            y += row_h + 6.0;
        }
        if scene_bank_indices(&self.model.world).is_empty() {
            draw_editor_text("No scenes exist yet", rect.x, y, 17.0, WARN);
        }
    }

    pub(crate) fn draw_scene_bank_workspace(&self) {
        let content_host = self.canvas_workspace_layout().context_toolbar;
        let viewport = self.scene_bank_viewport_rect();
        let indices = scene_bank_indices(&self.model.world);
        let selected_position = indices
            .iter()
            .position(|index| *index == self.selected_scene)
            .unwrap_or(0);
        let (columns, capacity, start, card_w) =
            scene_library_layout(viewport, indices.len(), selected_position);
        let end = (start + capacity).min(indices.len());

        draw_rectangle(
            content_host.x,
            content_host.y,
            content_host.w,
            content_host.h,
            editor_theme::colors::PANEL_BG,
        );
        draw_scissored_text(
            &format!(
                "Scene Library · {} scenes · showing {}–{}",
                indices.len(),
                if indices.is_empty() { 0 } else { start + 1 },
                end
            ),
            content_host.x + 10.0,
            content_host.y + 21.0,
            content_host.w - 20.0,
            13.0,
            TEXT,
        );
        draw_rectangle(
            viewport.x,
            viewport.y,
            viewport.w,
            viewport.h,
            Color::new(0.075, 0.085, 0.095, 1.0),
        );

        for (visible_position, scene_index) in indices
            .iter()
            .copied()
            .skip(start)
            .take(capacity)
            .enumerate()
        {
            let Some(scene) = self.model.world.scenes.get(scene_index) else {
                continue;
            };
            let card = scene_library_card_rect(viewport, visible_position, columns, card_w);
            let selected = scene_index == self.selected_scene;
            draw_rectangle(
                card.x,
                card.y,
                card.w,
                card.h,
                Color::new(0.085, 0.075, 0.065, 0.98),
            );
            let preview = Rect::new(card.x + 8.0, card.y + 34.0, card.w - 16.0, card.h - 62.0);
            draw_scene_into_rect(scene, preview);
            draw_rectangle(
                card.x,
                card.y,
                card.w,
                28.0,
                Color::new(0.035, 0.040, 0.048, 0.94),
            );
            draw_scissored_text(&scene.name, card.x + 8.0, card.y + 20.0, card.w - 16.0, 17.0, TEXT);
            draw_badge(
                Rect::new(card.x + 8.0, card.y + card.h - 25.0, 72.0, 18.0),
                scene.kind.code(),
                selected,
            );
            draw_scissored_text(
                &format!("{} • {} transitions", scene_bank_group(scene).label(), scene.transitions.len()),
                card.x + 88.0,
                card.y + card.h - 10.0,
                (card.w - 96.0).max(1.0),
                12.0,
                MUTED,
            );
            draw_rectangle_lines(
                card.x,
                card.y,
                card.w,
                card.h,
                if selected { 3.0 } else { 1.0 },
                if selected { GOOD } else { PANEL_EDGE },
            );
        }
        draw_rectangle_lines(viewport.x, viewport.y, viewport.w, viewport.h, 1.0, PANEL_EDGE);
        if indices.is_empty() {
            draw_editor_text(
                "No scenes exist yet. Create or import a scene from the Game Canvas document bar.",
                viewport.x + 16.0,
                viewport.y + 30.0,
                16.0,
                MUTED,
            );
        }
    }

    pub(crate) fn draw_scene_bank_inspector(&self, rect: Rect) {
        let Some(scene) = self.model.world.scenes.get(self.selected_scene) else {
            draw_editor_text("No scene selected", rect.x, rect.y, 20.0, MUTED);
            return;
        };
        let mut y = rect.y;
        draw_editor_text(&scene.name, rect.x, y + 22.0, 24.0, TEXT);
        draw_badge(
            Rect::new(rect.x, y + 32.0, 92.0, 20.0),
            scene.kind.code(),
            true,
        );
        y += 66.0;
        draw_section_header(Rect::new(rect.x, y, rect.w, 24.0), "Scene Details", None);
        y += 34.0;
        for line in [
            format!("ID: {}", scene.id.code()),
            format!("Kind: {}", scene.kind.code()),
            format!("Biome: {}", scene.biome.label()),
            format!("Objects: {}", scene.map.objects.len()),
            format!("Multi-tile stamps: {}", scene.map.stamps.len()),
            format!("Transitions: {}", scene.transitions.len()),
            format!("Browser group: {}", scene_bank_group(scene).label()),
            self.scene_stable_region_summary(scene),
            self.scene_reference_integrity_summary(scene),
            format!("Document: {} x {} tiles", MAP_W, MAP_H),
        ] {
            draw_editor_text(&line, rect.x, y, 17.0, TEXT);
            y += 24.0;
        }
        y += 6.0;
        for (index, label) in [
            "Open in Game Canvas",
            "Locate in World",
            "Duplicate Scene",
            "Validate References",
        ].into_iter().enumerate() {
            draw_editor_widget(
                scene_bank_action_button_rect(rect, index),
                label,
                false,
            );
        }
        y += 164.0;
        draw_section_header(Rect::new(rect.x, y, rect.w, 24.0), "Scene Browser Rules", None);
        y += 34.0;
        for line in [
            "World scenes locate back to their persistent world rectangle",
            "Interior/cave documents connect through stable scene references",
            "Duplicate creates a new stable ProjectSceneId and never reuses links",
            "Reference validation reports missing targets before destructive edits",
        ] {
            draw_editor_text(line, rect.x, y, 15.0, MUTED);
            y += 21.0;
        }
    }

    pub(crate) fn handle_scene_bank_canvas_click(&mut self, mx: f32, my: f32) -> bool {
        let viewport = self.scene_bank_viewport_rect();
        let point = vec2(mx, my);
        if !viewport.contains(point) {
            return false;
        }
        let indices = scene_bank_indices(&self.model.world);
        let selected_position = indices
            .iter()
            .position(|index| *index == self.selected_scene)
            .unwrap_or(0);
        let (columns, capacity, start, card_w) =
            scene_library_layout(viewport, indices.len(), selected_position);
        for (visible_position, scene_index) in indices
            .iter()
            .copied()
            .skip(start)
            .take(capacity)
            .enumerate()
        {
            if scene_library_card_rect(viewport, visible_position, columns, card_w).contains(point) {
                let scene_name = self.model.world.scenes[scene_index].name.clone();
                self.focus_scene_index_without_open(scene_index);
                self.status_message = format!("Selected Scene Library entry {scene_name}");
                return true;
            }
        }
        true
    }

    pub(crate) fn handle_scene_bank_list_click(&mut self, mx: f32, my: f32, rect: Rect) -> bool {
        let point = vec2(mx, my);
        if !rect.contains(point) {
            return false;
        }
        let relative = my - (rect.y + 12.0);
        if relative < 0.0 {
            return true;
        }
        let position = (relative / 50.0).floor() as usize;
        if let Some(scene_index) = scene_bank_indices(&self.model.world).get(position).copied() {
            let scene_name = self.model.world.scenes[scene_index].name.clone();
            self.focus_scene_index_without_open(scene_index);
            self.status_message = format!("Selected Scene Library entry {scene_name}");
        }
        true
    }

    pub(crate) fn handle_scene_bank_inspector_click(&mut self, mx: f32, my: f32) -> bool {
        let rect = self.inspector_content_rect();
        let point = vec2(mx, my);
        for index in 0..4 {
            let button = scene_bank_action_button_rect(rect, index);
            if !button.contains(point) { continue; }
            match index {
                0 => self.open_selected_scene_bank_scene(),
                1 => self.locate_selected_scene_in_world(),
                2 => self.duplicate_selected_scene(),
                3 => self.validate_selected_scene_references(),
                _ => unreachable!(),
            }
            return true;
        }
        false
    }

    fn scene_stable_region_summary(&self, scene: &haven_core::SceneMap) -> String {
        let Some(assignment) = self
            .scene_assignments
            .assignments
            .iter()
            .find(|assignment| assignment.scene_code == scene.id.code())
        else {
            return "Region: off-world / no persistent world region".to_string();
        };
        let Some(manifest) = self.scene_rectangles.as_ref() else {
            return "Region: world manifest unavailable".to_string();
        };
        let Some(rectangle) = manifest
            .scene_rectangles
            .iter()
            .find(|rectangle| rectangle.scene_id == assignment.rectangle_id)
        else {
            return "Region: assignment target missing".to_string();
        };
        haven_world::legacy_scene_rectangle_region_key(
            manifest.archipelago_generation.seed,
            rectangle,
        )
        .map(|key| format!("Region: {}", key.stable_id()))
        .unwrap_or_else(|| "Region: special/off-grid world scene".to_string())
    }

    fn scene_reference_integrity_summary(&self, scene: &haven_core::SceneMap) -> String {
        let dangling = scene
            .transitions
            .iter()
            .filter(|transition| self.model.world.scene_by_reference(&transition.target).is_none())
            .count();
        let inbound = self
            .model
            .world
            .scenes
            .iter()
            .flat_map(|candidate| candidate.transitions.iter())
            .filter(|transition| self.model.world.scene_by_reference(&transition.target).is_some_and(|target| target.id == scene.id))
            .count();
        let assigned = self
            .scene_assignments
            .assignments
            .iter()
            .any(|assignment| assignment.scene_code == scene.id.code());
        format!(
            "References: {} inbound • {} dangling outbound • {}",
            inbound,
            dangling,
            if assigned { "world-located" } else { "off-world/unassigned" }
        )
    }

    pub(crate) fn validate_selected_scene_references(&mut self) {
        let Some(scene) = self.model.world.scenes.get(self.selected_scene) else {
            self.status_message = "No scene selected".to_string();
            return;
        };
        let summary = self.scene_reference_integrity_summary(scene);
        self.status_message = format!("{} · {}", scene.name, summary);
    }

    pub(crate) fn locate_selected_scene_in_world(&mut self) {
        let Some(scene) = self.model.world.scenes.get(self.selected_scene) else {
            self.status_message = "No scene selected".to_string();
            return;
        };
        let scene_id = scene.id.clone();
        let scene_name = scene.name.clone();
        let Some(assignment) = self
            .scene_assignments
            .assignments
            .iter()
            .find(|assignment| assignment.scene_code == scene_id.code())
            .cloned()
        else {
            self.status_message = format!("{scene_name} is an off-world scene with no world rectangle assignment");
            return;
        };
        let Some(manifest) = self.scene_rectangles.as_ref() else {
            self.status_message = "Development World manifest is unavailable".to_string();
            return;
        };
        let Some((rectangle_index, rectangle)) = manifest
            .scene_rectangles
            .iter()
            .enumerate()
            .find(|(_, rectangle)| rectangle.scene_id == assignment.rectangle_id)
        else {
            self.status_message = format!("{scene_name} assignment points to a missing world rectangle");
            return;
        };
        let Some(bake) = self.development_world_semantic_bake.as_ref() else {
            self.status_message = "Development World has no canonical semantic world bake".to_string();
            return;
        };
        let Some(bounds) = world_archipelago_overview_bounds(bake) else {
            self.status_message = "Development World semantic bake has invalid bounds".to_string();
            return;
        };
        let target = super::world_surface_editor::world_overview_landmass_rect(
            &self.development_world_settings,
            rectangle.landmass_id,
        )
        .unwrap_or(bounds);
        self.selected_rectangle = rectangle_index;
        self.selected_landmass_id = rectangle.landmass_id;
        self.world_show_entire_world = true;
        self.viewport_mode = EditorViewportMode::SceneRectangles;
        let viewport = self.world_canvas_viewport_rect();
        self.world_canvas.frame_rect(viewport, bounds, target);
        self.sync_assignment_cycles_to_selected_rectangle();
        self.status_message = format!("Located {scene_name} in the authoritative Development World");
    }

    pub(crate) fn cycle_scene_bank_selection(&mut self, delta: i32) {
        let indices = scene_bank_indices(&self.model.world);
        if indices.is_empty() {
            return;
        }
        let current = indices
            .iter()
            .position(|index| *index == self.selected_scene)
            .unwrap_or(0) as i32;
        let next = (current + delta).rem_euclid(indices.len() as i32) as usize;
        self.focus_scene_index_without_open(indices[next]);
    }

    pub(crate) fn open_selected_scene_bank_scene(&mut self) {
        let Some(scene) = self.model.world.scenes.get(self.selected_scene) else {
            return;
        };
        let name = scene.name.clone();
        self.ensure_selected_scene_document_open();
        self.viewport_mode = EditorViewportMode::SceneMap;
        self.status_message = format!("Opened {name} in Game Canvas");
    }
}
