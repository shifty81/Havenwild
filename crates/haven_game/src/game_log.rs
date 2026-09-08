use macroquad::prelude::get_time;
use std::fs::{create_dir_all, OpenOptions};
use std::io::Write;
use std::path::PathBuf;
use std::time::{SystemTime, UNIX_EPOCH};

use crate::runtime_config::runtime_root;

pub(crate) struct GameLog {
    rolling_file: Option<std::fs::File>,
    session_file: Option<std::fs::File>,
    session_path: Option<PathBuf>,
}

impl GameLog {
    pub(crate) fn new() -> Self {
        let log_root = runtime_root().join("logs");
        let _ = create_dir_all(&log_root);
        let rolling_file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(log_root.join("haven_game.log"))
            .ok();
        let session_path = log_root.join(format!("haven_game_{}.log", log_stamp()));
        let session_file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(&session_path)
            .ok();
        let mut log = Self {
            rolling_file,
            session_file,
            session_path: Some(session_path),
        };
        log.event("Game log session opened");
        if let Some(path) = log.session_path.clone() {
            log.event(&format!("Session log path: {}", path.display()));
        }
        log
    }

    pub(crate) fn event(&mut self, message: &str) {
        let line = format!("[{} | {:.2}] {}", log_stamp(), get_time(), message);
        if let Some(file) = &mut self.rolling_file {
            let _ = writeln!(file, "{line}");
            let _ = file.flush();
        }
        if let Some(file) = &mut self.session_file {
            let _ = writeln!(file, "{line}");
            let _ = file.flush();
        }
    }
}

fn log_stamp() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_secs())
        .unwrap_or_default()
}
