//! Shared background-work vocabulary.
//!
//! Rayon is the first activated OSS foundation dependency in W62. The editor
//! talks to Havenwild JobRecord/JobBatch APIs instead of exposing Rayon types.

use haven_identity::HavenId;
use rayon::prelude::*;
use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum JobState {
    Queued,
    Running,
    Completed,
    Failed,
    Cancelled,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct JobRecord {
    pub id: HavenId,
    pub label: String,
    pub state: JobState,
    pub progress: f32,
    #[serde(default)]
    pub detail: String,
}

impl JobRecord {
    pub fn queued(label: impl Into<String>) -> Self {
        Self {
            id: HavenId::new("job"),
            label: label.into(),
            state: JobState::Queued,
            progress: 0.0,
            detail: String::new(),
        }
    }
}

pub fn parallel_map<T, R, F>(items: &[T], operation: F) -> Vec<R>
where
    T: Sync,
    R: Send,
    F: Fn(&T) -> R + Sync + Send,
{
    items.par_iter().map(operation).collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rayon_adapter_preserves_result_count() {
        let input = [1_i32, 2, 3, 4];
        let output = parallel_map(&input, |value| value * value);
        assert_eq!(output, vec![1, 4, 9, 16]);
    }
}
