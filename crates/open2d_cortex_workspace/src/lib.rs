//! Workspace-safe source access and reversible Cortex transactions.

use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;
use std::fs;
use std::io;
use std::path::{Component, Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Clone, Debug)]
pub struct Workspace {
    root: PathBuf,
}

impl Workspace {
    pub fn open(root: impl AsRef<Path>) -> Result<Self, WorkspaceError> {
        let root = fs::canonicalize(root).map_err(WorkspaceError::Io)?;
        if !root.join("Cargo.toml").is_file() {
            return Err(WorkspaceError::Invalid("workspace root must contain Cargo.toml".into()));
        }
        Ok(Self { root })
    }

    pub fn root(&self) -> &Path { &self.root }

    pub fn resolve(&self, relative: impl AsRef<Path>) -> Result<PathBuf, WorkspaceError> {
        let relative = relative.as_ref();
        if relative.is_absolute() {
            return Err(WorkspaceError::UnsafePath(relative.display().to_string()));
        }
        if relative.components().any(|part| matches!(part, Component::ParentDir | Component::RootDir | Component::Prefix(_))) {
            return Err(WorkspaceError::UnsafePath(relative.display().to_string()));
        }
        Ok(self.root.join(relative))
    }

    pub fn read_text(&self, relative: impl AsRef<Path>, max_bytes: usize) -> Result<String, WorkspaceError> {
        let path = self.resolve(relative)?;
        let meta = fs::metadata(&path).map_err(WorkspaceError::Io)?;
        if meta.len() > max_bytes as u64 {
            return Err(WorkspaceError::Invalid(format!("file exceeds read limit: {}", path.display())));
        }
        fs::read_to_string(path).map_err(WorkspaceError::Io)
    }

    pub fn list_files(&self, relative: impl AsRef<Path>, max_files: usize) -> Result<Vec<PathBuf>, WorkspaceError> {
        let base = self.resolve(relative)?;
        let mut result = Vec::new();
        collect_files(&self.root, &base, max_files, &mut result)?;
        result.sort();
        Ok(result)
    }

    pub fn search_text(
        &self,
        query: &str,
        roots: &[PathBuf],
        max_hits: usize,
    ) -> Result<Vec<SearchHit>, WorkspaceError> {
        if query.is_empty() { return Err(WorkspaceError::Invalid("search query is empty".into())); }
        let mut hits = Vec::new();
        let search_roots = if roots.is_empty() { vec![PathBuf::new()] } else { roots.to_vec() };
        for relative_root in search_roots {
            for relative in self.list_files(relative_root, 20_000)? {
                if hits.len() >= max_hits { break; }
                if !looks_textual(&relative) { continue; }
                let absolute = self.resolve(&relative)?;
                let Ok(text) = fs::read_to_string(&absolute) else { continue; };
                for (line_index, line) in text.lines().enumerate() {
                    if line.contains(query) {
                        hits.push(SearchHit {
                            path: relative.clone(),
                            line: line_index + 1,
                            preview: line.trim().chars().take(240).collect(),
                        });
                        if hits.len() >= max_hits { break; }
                    }
                }
            }
        }
        Ok(hits)
    }
}

fn collect_files(root: &Path, dir: &Path, max_files: usize, result: &mut Vec<PathBuf>) -> Result<(), WorkspaceError> {
    if result.len() >= max_files || !dir.exists() { return Ok(()); }
    for entry in fs::read_dir(dir).map_err(WorkspaceError::Io)? {
        let entry = entry.map_err(WorkspaceError::Io)?;
        let path = entry.path();
        if path.file_name().and_then(|v| v.to_str()).map(is_ignored_dir).unwrap_or(false) && path.is_dir() {
            continue;
        }
        if path.is_dir() {
            collect_files(root, &path, max_files, result)?;
        } else if path.is_file() {
            let rel = path.strip_prefix(root).map_err(|_| WorkspaceError::UnsafePath(path.display().to_string()))?;
            result.push(rel.to_path_buf());
            if result.len() >= max_files { break; }
        }
    }
    Ok(())
}

fn is_ignored_dir(name: &str) -> bool {
    matches!(name, ".git" | ".open2d" | "target" | "node_modules" | "build" | "builds" | "dist" | "logs")
}

fn looks_textual(path: &Path) -> bool {
    matches!(
        path.extension().and_then(|v| v.to_str()).unwrap_or_default().to_ascii_lowercase().as_str(),
        "rs" | "toml" | "json" | "md" | "txt" | "cmd" | "ps1" | "ts" | "js" | "yml" | "yaml" | "ron"
    )
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct SearchHit {
    pub path: PathBuf,
    pub line: usize,
    pub preview: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
struct TransactionManifest {
    id: String,
    state: TransactionState,
    touched: BTreeSet<PathBuf>,
    created: BTreeSet<PathBuf>,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
enum TransactionState { Active, Committed, RolledBack }

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct TransactionSummary {
    pub id: String,
    pub touched: Vec<PathBuf>,
    pub created: Vec<PathBuf>,
}

pub struct TransactionManager {
    workspace: Workspace,
    transaction_root: PathBuf,
    active: Option<TransactionManifest>,
}

impl TransactionManager {
    pub fn new(workspace: Workspace) -> Result<Self, WorkspaceError> {
        let transaction_root = workspace.root.join(".open2d").join("cortex").join("transactions");
        fs::create_dir_all(&transaction_root).map_err(WorkspaceError::Io)?;
        let active = load_active_transaction(&transaction_root)?;
        Ok(Self { workspace, transaction_root, active })
    }

    pub fn begin(&mut self, label: &str) -> Result<String, WorkspaceError> {
        if self.active.is_some() {
            return Err(WorkspaceError::Invalid("a Cortex transaction is already active".into()));
        }
        let id = format!("{}-{}-{}", unix_millis(), std::process::id(), sanitize(label));
        let manifest = TransactionManifest {
            id: id.clone(),
            state: TransactionState::Active,
            touched: BTreeSet::new(),
            created: BTreeSet::new(),
        };
        fs::create_dir_all(self.transaction_dir(&id).join("backup")).map_err(WorkspaceError::Io)?;
        self.active = Some(manifest);
        self.persist_active()?;
        Ok(id)
    }

    pub fn active_id(&self) -> Option<&str> { self.active.as_ref().map(|tx| tx.id.as_str()) }

    pub fn active_summary(&self) -> Option<TransactionSummary> {
        self.active.as_ref().map(|tx| TransactionSummary {
            id: tx.id.clone(),
            touched: tx.touched.iter().cloned().collect(),
            created: tx.created.iter().cloned().collect(),
        })
    }

    pub fn checkpoint_path(&mut self, relative: impl AsRef<Path>) -> Result<(), WorkspaceError> {
        let relative = normalize_relative(relative.as_ref())?;
        self.checkpoint(&relative)?;
        self.persist_active()
    }

    pub fn write_text(&mut self, relative: impl AsRef<Path>, content: &str) -> Result<(), WorkspaceError> {
        let relative = normalize_relative(relative.as_ref())?;
        self.checkpoint(&relative)?;
        let path = self.workspace.resolve(&relative)?;
        if let Some(parent) = path.parent() { fs::create_dir_all(parent).map_err(WorkspaceError::Io)?; }
        fs::write(path, content.as_bytes()).map_err(WorkspaceError::Io)?;
        self.persist_active()
    }

    pub fn replace_text(
        &mut self,
        relative: impl AsRef<Path>,
        old: &str,
        new: &str,
        expected_occurrences: usize,
    ) -> Result<usize, WorkspaceError> {
        let relative = normalize_relative(relative.as_ref())?;
        let text = self.workspace.read_text(&relative, 4 * 1024 * 1024)?;
        let count = text.matches(old).count();
        if count != expected_occurrences {
            return Err(WorkspaceError::Invalid(format!(
                "replace guard failed for {}: expected {expected_occurrences} occurrences, found {count}",
                relative.display()
            )));
        }
        let updated = text.replace(old, new);
        self.write_text(relative, &updated)?;
        Ok(count)
    }

    pub fn commit(&mut self) -> Result<Option<String>, WorkspaceError> {
        let Some(mut tx) = self.active.take() else { return Ok(None); };
        tx.state = TransactionState::Committed;
        persist_manifest(&self.transaction_dir(&tx.id), &tx)?;
        Ok(Some(tx.id))
    }

    pub fn rollback(&mut self) -> Result<Option<String>, WorkspaceError> {
        let Some(mut tx) = self.active.take() else { return Ok(None); };
        let tx_dir = self.transaction_dir(&tx.id);
        for relative in tx.touched.iter().rev() {
            let backup = tx_dir.join("backup").join(relative);
            let destination = self.workspace.resolve(relative)?;
            if backup.exists() {
                if let Some(parent) = destination.parent() { fs::create_dir_all(parent).map_err(WorkspaceError::Io)?; }
                fs::copy(&backup, &destination).map_err(WorkspaceError::Io)?;
            }
        }
        for relative in tx.created.iter().rev() {
            let destination = self.workspace.resolve(relative)?;
            if destination.is_file() { fs::remove_file(destination).map_err(WorkspaceError::Io)?; }
        }
        tx.state = TransactionState::RolledBack;
        persist_manifest(&tx_dir, &tx)?;
        Ok(Some(tx.id))
    }

    fn checkpoint(&mut self, relative: &Path) -> Result<(), WorkspaceError> {
        let Some(tx) = self.active.as_mut() else {
            return Err(WorkspaceError::Invalid("write requested without an active Cortex transaction".into()));
        };
        if tx.touched.contains(relative) || tx.created.contains(relative) { return Ok(()); }
        let source = self.workspace.resolve(relative)?;
        if source.exists() {
            let backup = self.transaction_root.join(&tx.id).join("backup").join(relative);
            if let Some(parent) = backup.parent() { fs::create_dir_all(parent).map_err(WorkspaceError::Io)?; }
            fs::copy(source, backup).map_err(WorkspaceError::Io)?;
            tx.touched.insert(relative.to_path_buf());
        } else {
            tx.created.insert(relative.to_path_buf());
        }
        Ok(())
    }

    fn persist_active(&self) -> Result<(), WorkspaceError> {
        if let Some(tx) = &self.active {
            persist_manifest(&self.transaction_dir(&tx.id), tx)?;
        }
        Ok(())
    }

    fn transaction_dir(&self, id: &str) -> PathBuf { self.transaction_root.join(id) }
}

fn load_active_transaction(
    transaction_root: &Path,
) -> Result<Option<TransactionManifest>, WorkspaceError> {
    let mut active = Vec::<TransactionManifest>::new();
    for entry in fs::read_dir(transaction_root).map_err(WorkspaceError::Io)? {
        let entry = entry.map_err(WorkspaceError::Io)?;
        if !entry.path().is_dir() {
            continue;
        }
        let manifest_path = entry.path().join("transaction.json");
        if !manifest_path.is_file() {
            continue;
        }
        let bytes = fs::read(&manifest_path).map_err(WorkspaceError::Io)?;
        let manifest: TransactionManifest = serde_json::from_slice(&bytes)
            .map_err(|error| WorkspaceError::Invalid(format!(
                "invalid transaction manifest {}: {error}",
                manifest_path.display()
            )))?;
        if manifest.state == TransactionState::Active {
            active.push(manifest);
        }
    }

    active.sort_by(|a, b| a.id.cmp(&b.id));
    match active.len() {
        0 => Ok(None),
        1 => Ok(active.pop()),
        count => Err(WorkspaceError::Invalid(format!(
            "found {count} active Cortex transactions; resolve transaction manifests before continuing"
        ))),
    }
}

fn persist_manifest(dir: &Path, tx: &TransactionManifest) -> Result<(), WorkspaceError> {
    fs::create_dir_all(dir).map_err(WorkspaceError::Io)?;
    let bytes = serde_json::to_vec_pretty(tx).map_err(|error| WorkspaceError::Invalid(error.to_string()))?;
    fs::write(dir.join("transaction.json"), bytes).map_err(WorkspaceError::Io)
}

fn normalize_relative(path: &Path) -> Result<PathBuf, WorkspaceError> {
    if path.is_absolute() || path.components().any(|part| matches!(part, Component::ParentDir | Component::RootDir | Component::Prefix(_))) {
        return Err(WorkspaceError::UnsafePath(path.display().to_string()));
    }
    Ok(path.to_path_buf())
}

fn unix_millis() -> u128 {
    SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_millis()
}

fn sanitize(value: &str) -> String {
    let text: String = value.chars().map(|c| if c.is_ascii_alphanumeric() || c == '-' || c == '_' { c } else { '-' }).collect();
    if text.is_empty() { "transaction".into() } else { text }
}

#[derive(Debug)]
pub enum WorkspaceError {
    Io(io::Error),
    UnsafePath(String),
    Invalid(String),
}

impl std::fmt::Display for WorkspaceError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Io(error) => write!(f, "{error}"),
            Self::UnsafePath(path) => write!(f, "unsafe workspace path: {path}"),
            Self::Invalid(message) => f.write_str(message),
        }
    }
}
impl std::error::Error for WorkspaceError {}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn parent_paths_are_rejected() {
        assert!(normalize_relative(Path::new("../outside")).is_err());
    }
}
