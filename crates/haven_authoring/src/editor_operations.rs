use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum EditorJobKind {
    Build,
    Validation,
    AssetRefresh,
    Import,
    Export,
    WorldBake,
    RuntimeLaunch,
    BackgroundAnalysis,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum EditorJobState {
    Queued,
    Running,
    Passed,
    Failed,
    Cancelled,
}

impl EditorJobState {
    pub const fn is_terminal(self) -> bool {
        matches!(self, Self::Passed | Self::Failed | Self::Cancelled)
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct EditorJobRecord {
    pub id: String,
    pub label: String,
    pub kind: EditorJobKind,
    pub state: EditorJobState,
    pub progress_permille: u16,
    #[serde(default)]
    pub message: String,
    #[serde(default)]
    pub log_path: Option<String>,
}

impl EditorJobRecord {
    pub fn set_progress(&mut self, progress_permille: u16) {
        self.progress_permille = progress_permille.min(1000);
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum EditorProblemSeverity {
    Info,
    Warning,
    Error,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct EditorProblem {
    pub code: String,
    pub message: String,
    pub severity: EditorProblemSeverity,
    #[serde(default)]
    pub source: Option<String>,
    #[serde(default)]
    pub relative_path: Option<String>,
    #[serde(default)]
    pub line: Option<u32>,
    #[serde(default)]
    pub job_id: Option<String>,
}

#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct EditorOperationsSnapshot {
    pub jobs: Vec<EditorJobRecord>,
    pub problems: Vec<EditorProblem>,
}

impl EditorOperationsSnapshot {
    pub fn active_job_count(&self) -> usize {
        self.jobs.iter().filter(|job| !job.state.is_terminal()).count()
    }

    pub fn blocking_problem_count(&self) -> usize {
        self.problems
            .iter()
            .filter(|problem| problem.severity == EditorProblemSeverity::Error)
            .count()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn progress_is_bounded_and_terminal_jobs_are_not_active() {
        let mut job = EditorJobRecord {
            id: "job-1".into(),
            label: "Build".into(),
            kind: EditorJobKind::Build,
            state: EditorJobState::Running,
            progress_permille: 0,
            message: String::new(),
            log_path: None,
        };
        job.set_progress(5000);
        assert_eq!(job.progress_permille, 1000);
        job.state = EditorJobState::Passed;
        let snapshot = EditorOperationsSnapshot { jobs: vec![job], problems: Vec::new() };
        assert_eq!(snapshot.active_job_count(), 0);
    }
}
