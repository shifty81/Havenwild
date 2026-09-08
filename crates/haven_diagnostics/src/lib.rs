//! Project-wide structured diagnostics boundary.
//!
//! This zero-surprise foundation is deliberately independent of any concrete
//! tracing/profiler backend. `tracing`, sysinfo and puffin can plug in behind
//! the Havenwild event/metric vocabulary after the first green integration gate.

use haven_identity::HavenId;
use serde::{Deserialize, Serialize};
use std::collections::VecDeque;
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum DiagnosticLevel {
    Trace,
    Info,
    Warning,
    Error,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct DiagnosticEvent {
    pub id: HavenId,
    pub unix_millis: u128,
    pub level: DiagnosticLevel,
    pub category: String,
    pub message: String,
    #[serde(default)]
    pub project_id: Option<String>,
    #[serde(default)]
    pub document_id: Option<String>,
    #[serde(default)]
    pub scene_id: Option<String>,
    #[serde(default)]
    pub command_id: Option<String>,
    #[serde(default)]
    pub job_id: Option<String>,
}

impl DiagnosticEvent {
    pub fn new(level: DiagnosticLevel, category: impl Into<String>, message: impl Into<String>) -> Self {
        let unix_millis = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|duration| duration.as_millis())
            .unwrap_or_default();
        Self {
            id: HavenId::new("diag"),
            unix_millis,
            level,
            category: category.into(),
            message: message.into(),
            project_id: None,
            document_id: None,
            scene_id: None,
            command_id: None,
            job_id: None,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct MetricSnapshot {
    pub frame_ms: f32,
    pub update_ms: f32,
    pub draw_ms: f32,
    pub background_jobs_active: u32,
    pub background_jobs_queued: u32,
    pub asset_count: u32,
}

#[derive(Clone, Debug)]
pub struct DiagnosticsHub {
    capacity: usize,
    events: VecDeque<DiagnosticEvent>,
    metrics: MetricSnapshot,
}

impl Default for DiagnosticsHub {
    fn default() -> Self {
        Self::new(256)
    }
}

impl DiagnosticsHub {
    pub fn new(capacity: usize) -> Self {
        Self {
            capacity: capacity.max(16),
            events: VecDeque::new(),
            metrics: MetricSnapshot::default(),
        }
    }

    pub fn emit(&mut self, event: DiagnosticEvent) {
        while self.events.len() >= self.capacity {
            self.events.pop_front();
        }
        self.events.push_back(event);
    }

    pub fn recent(&self) -> impl DoubleEndedIterator<Item = &DiagnosticEvent> {
        self.events.iter()
    }

    pub fn set_metrics(&mut self, metrics: MetricSnapshot) {
        self.metrics = metrics;
    }

    pub fn metrics(&self) -> MetricSnapshot {
        self.metrics
    }

    pub fn error_count(&self) -> usize {
        self.events.iter().filter(|event| event.level == DiagnosticLevel::Error).count()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn hub_is_bounded() {
        let mut hub = DiagnosticsHub::new(16);
        for index in 0..40 {
            hub.emit(DiagnosticEvent::new(DiagnosticLevel::Info, "test", index.to_string()));
        }
        assert_eq!(hub.recent().count(), 16);
    }
}
