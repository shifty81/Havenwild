use haven_save::CharacterAppearance;
use std::{collections::HashMap, process::Command};

use crate::character_creator_model::{appearance_diagnostics, StarterCreatorSelection};
use macroquad::prelude::*;

// Pass167Z109Q: behavior-preserving frontend source extraction.
include!("client_character_frontend_preview.rs");
include!("client_character_frontend_chrome.rs");
include!("client_character_frontend_layout.rs");
