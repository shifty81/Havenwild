//! Curated project-aware Cortex tool broker.

use cortex_adapter_git::GitAdapter;
use cortex_adapter_open2d::Open2DAdapter;
use cortex_plugin::{Permission, PermissionPolicy, PluginRegistry};
use cortex_vault::Vault;
use open2d_cortex_capture::CaptureService;
use open2d_cortex_image::{
    catalog_path_from_state, generated_output_root_from_state, metadata_root_from_state,
    ImageArtifactCatalog,
};
use open2d_cortex_process::ProcessService;
use open2d_cortex_rpc::{call as rpc_call, default_address, request_with_token as rpc_request_with_token};
use open2d_cortex_protocol::{
    EmbeddingProvider, ImageArtifactStatus, ImageGenerationRequest, ImageProvider, ToolCall,
    ToolDefinition, ToolExecutor, ToolResultInput, VisionProvider,
};
use open2d_cortex_workspace::{TransactionManager, Workspace};
use open2d_dev_session::DevSession;
use open2d_runtime_bridge::read_snapshot;
use serde_json::{json, Value};
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

pub struct ToolBroker {
    workspace: Workspace,
    transactions: TransactionManager,
    processes: ProcessService,
    vault: Vault,
    embedding_provider: Option<Box<dyn EmbeddingProvider>>,
    permissions: PermissionPolicy,
    session: DevSession,
    capture: CaptureService,
    image_catalog: ImageArtifactCatalog,
    image_provider: Option<Box<dyn ImageProvider>>,
    vision_provider: Option<Box<dyn VisionProvider>>,
    open2d: Option<Open2DAdapter>,
    git: Option<GitAdapter>,
}

impl ToolBroker {
    pub fn new(
        project_root: impl AsRef<Path>,
        image_provider: Option<Box<dyn ImageProvider>>,
        vision_provider: Option<Box<dyn VisionProvider>>,
        embedding_provider: Option<Box<dyn EmbeddingProvider>>,
    ) -> Result<Self, String> {
        let workspace = Workspace::open(project_root.as_ref()).map_err(|e| e.to_string())?;
        let transactions = TransactionManager::new(workspace.clone()).map_err(|e| e.to_string())?;
        let files = workspace.list_files("", 20_000).map_err(|e| e.to_string())?;
        let vault_path = workspace
            .cortex_state_dir()
            .join("vault")
            .join("vault.json");
        let vault = if vault_path.is_file() {
            Vault::load(&vault_path)
                .unwrap_or_else(|_| Vault::build_lexical(workspace.root(), &files, 512 * 1024))
        } else {
            Vault::build_lexical(workspace.root(), &files, 512 * 1024)
        };
        let permission_path = workspace.cortex_state_dir().join("permissions.json");
        let permissions = PermissionPolicy::load_or_default(&permission_path)?;
        if !permission_path.is_file() {
            permissions.save(&permission_path)?;
        }
        let session = DevSession::create_in(
            workspace.root(),
            workspace.sessions_dir(),
            "cortex",
        )?;
        let capture = CaptureService::new(workspace.root().to_path_buf());
        let image_catalog =
            ImageArtifactCatalog::load(&catalog_path_from_state(&workspace.cortex_state_dir()))?;
        let open2d = Open2DAdapter::detect(workspace.root());
        let git = GitAdapter::detect(workspace.root());
        Ok(Self {
            workspace,
            transactions,
            processes: ProcessService::default(),
            vault,
            embedding_provider,
            permissions,
            session,
            capture,
            image_catalog,
            image_provider,
            vision_provider,
            open2d,
            git,
        })
    }

    pub fn workspace_root(&self) -> &Path { self.workspace.root() }
    pub fn session(&self) -> &DevSession { &self.session }

    fn workspace_status(&self) -> Result<Value, String> {
        let cargo_toml = if self.workspace.root().join("Cargo.toml").is_file() {
            Some(
                self.workspace
                    .read_text("Cargo.toml", 1024 * 1024)
                    .map_err(|error| error.to_string())?,
            )
        } else {
            None
        };
        let manifest_path = self
            .workspace
            .resolve("SOURCE_MANIFEST.json")
            .map_err(|error| error.to_string())?;
        let source_manifest = if manifest_path.is_file() {
            serde_json::from_slice::<Value>(
                &std::fs::read(manifest_path).map_err(|error| error.to_string())?,
            )
            .unwrap_or(Value::Null)
        } else {
            Value::Null
        };
        Ok(json!({
            "root": self.workspace.root(),
            "profile": self.workspace.profile(),
            "cargo_toml": cargo_toml,
            "source_manifest": source_manifest,
            "active_transaction": self.transactions.active_id(),
            "session_id": self.session.id.clone(),
            "state_directory": self.workspace.cortex_state_dir(),
            "adapters": {
                "open2d": self.open2d.as_ref().map(Open2DAdapter::status),
                "git": self.git.as_ref().map(|_| "active")
            },
            "vault": self.vault.status(),
            "permissions": self.permissions,
            "plugins": PluginRegistry::discover(
                self.workspace.root(),
                &self.workspace.cortex_state_dir()
            ).unwrap_or_default().len()
        }))
    }


    fn authorize_tool(&self, name: &str) -> Result<(), String> {
        let permission = if name.starts_with("source.") {
            if matches!(
                name,
                "source.list"
                    | "source.read"
                    | "source.search"
                    | "source.transaction_status"
                    | "source.transaction_files"
            ) {
                Permission::WorkspaceRead
            } else {
                Permission::WorkspaceWrite
            }
        } else if name.starts_with("build.") || name.starts_with("runtime.") {
            Permission::ProcessExecute
        } else if name.starts_with("git.") {
            Permission::GitRead
        } else if name.starts_with("vision.") || name.starts_with("capture.") {
            Permission::Vision
        } else if name.starts_with("image.") {
            Permission::ImageGeneration
        } else if name.starts_with("vscode.") {
            if matches!(name, "vscode.apply_workspace_edit" | "vscode.save_all") {
                Permission::WorkspaceWrite
            } else {
                Permission::WorkspaceRead
            }
        } else {
            Permission::WorkspaceRead
        };
        if self.permissions.granted.contains(&permission) {
            Ok(())
        } else {
            Err(format!(
                "Cortex permission denied for tool `{name}`: {:?}",
                permission
            ))
        }
    }

    fn require_rust_workspace(&self) -> Result<(), String> {
        if self.workspace.root().join("Cargo.toml").is_file() {
            Ok(())
        } else {
            Err("active workspace is not a Cargo/Rust workspace".into())
        }
    }

    fn call_vscode(&self, method: &str, params: Value) -> Result<Value, String> {
        let port = std::env::var("CORTEX_VSCODE_RPC_PORT")
            .or_else(|_| std::env::var("OPEN2D_VSCODE_RPC_PORT"))
            .ok()
            .and_then(|value| value.parse::<u16>().ok())
            .unwrap_or(7338);
        let id = format!("cortex-vscode-{}-{}", std::process::id(), unix_ms());
        let token_path = self.workspace.cortex_state_dir().join("rpc.token");
        let token = std::fs::read_to_string(&token_path)
            .map_err(|e| format!("Cortex RPC token unavailable at {}: {e}", token_path.display()))?;
        let response = rpc_call(
            default_address(port),
            &rpc_request_with_token(id, method, params, token.trim().to_string()),
        )?;
        if response.ok {
            Ok(response.result)
        } else {
            Err(response.error.unwrap_or_else(|| "VS Code bridge request failed".into()))
        }
    }

    fn execute_inner(&mut self, call: &ToolCall) -> Result<Value, String> {
        self.authorize_tool(&call.name)?;
        match call.name.as_str() {
            "workspace.status" | "project.status" => self.workspace_status(),
            "source.list" => {
                let path = arg_string(&call.arguments, "path").unwrap_or_default();
                let max = arg_u64(&call.arguments, "max_files").unwrap_or(400).clamp(1, 2_000) as usize;
                let files = self.workspace.list_files(path, max).map_err(|e| e.to_string())?;
                Ok(json!({"files": files}))
            }
            "source.read" => {
                let path = required_string(&call.arguments, "path")?;
                let max = arg_u64(&call.arguments, "max_bytes").unwrap_or(64 * 1024).clamp(1, 256 * 1024) as usize;
                let text = self.workspace.read_text(path, max).map_err(|e| e.to_string())?;
                Ok(json!({"text": text}))
            }
            "source.search" => {
                let query = required_string(&call.arguments, "query")?;
                let max_hits = arg_u64(&call.arguments, "max_hits").unwrap_or(50).clamp(1, 250) as usize;
                let roots = call.arguments.get("roots").and_then(Value::as_array)
                    .map(|items| items.iter().filter_map(Value::as_str).map(PathBuf::from).collect::<Vec<_>>())
                    .unwrap_or_default();
                let hits = self.workspace.search_text(query, &roots, max_hits).map_err(|e| e.to_string())?;
                Ok(json!({"hits": hits}))
            }
            "source.transaction_status" => {
                Ok(json!({"transaction": self.transactions.active_summary()}))
            }
            "source.transaction_files" => {
                let summary = self.transactions.active_summary();
                Ok(json!({
                    "transaction_id": summary.as_ref().map(|value| value.id.clone()),
                    "touched": summary.as_ref().map(|value| value.touched.clone()).unwrap_or_default(),
                    "created": summary.as_ref().map(|value| value.created.clone()).unwrap_or_default()
                }))
            }
            "source.checkpoint" => {
                let path = required_string(&call.arguments, "path")?;
                self.transactions.checkpoint_path(path).map_err(|e| e.to_string())?;
                Ok(json!({"checkpointed": path}))
            }
            "source.begin_transaction" => {
                let label = arg_string(&call.arguments, "label").unwrap_or_else(|| "agent-edit".into());
                let id = self.transactions.begin(&label).map_err(|e| e.to_string())?;
                Ok(json!({"transaction_id": id}))
            }
            "source.write_text" => {
                let path = required_string(&call.arguments, "path")?;
                let content = required_string(&call.arguments, "content")?;
                self.transactions.write_text(path, content).map_err(|e| e.to_string())?;
                Ok(json!({"written": true}))
            }
            "source.replace_text" => {
                let path = required_string(&call.arguments, "path")?;
                let old = required_string(&call.arguments, "old")?;
                let new = required_string(&call.arguments, "new")?;
                let expected = arg_u64(&call.arguments, "expected_occurrences").unwrap_or(1) as usize;
                let replaced = self.transactions.replace_text(path, old, new, expected).map_err(|e| e.to_string())?;
                Ok(json!({"replaced": replaced}))
            }
            "source.commit" => {
                let id = self.transactions.commit().map_err(|e| e.to_string())?;
                let committed = id.is_some();
                Ok(json!({"transaction_id": id, "committed": committed}))
            }
            "source.rollback" => {
                let id = self.transactions.rollback().map_err(|e| e.to_string())?;
                let rolled_back = id.is_some();
                Ok(json!({"transaction_id": id, "rolled_back": rolled_back}))
            }
            "build.cargo_fmt_check" => {
                self.require_rust_workspace()?;
                let result = self.processes.run_capture(
                    self.workspace.root(),
                    "cargo",
                    &["fmt", "--all", "--", "--check"],
                    false,
                )?;
                Ok(serde_json::to_value(result).map_err(|e| e.to_string())?)
            }
            "build.cargo_check" => {
                self.require_rust_workspace()?;
                let result = self.processes.run_cargo(self.workspace.root(), &["check", "--workspace", "--message-format=json"])?;
                Ok(serde_json::to_value(result).map_err(|e| e.to_string())?)
            }
            "build.cargo_test" => {
                self.require_rust_workspace()?;
                let result = self.processes.run_cargo(self.workspace.root(), &["test", "--workspace", "--no-run", "--message-format=json"])?;
                Ok(serde_json::to_value(result).map_err(|e| e.to_string())?)
            }
            "build.cargo_test_run" => {
                self.require_rust_workspace()?;
                let result = self.processes.run_capture(
                    self.workspace.root(),
                    "cargo",
                    &["test", "--workspace"],
                    false,
                )?;
                Ok(serde_json::to_value(result).map_err(|e| e.to_string())?)
            }
            "build.clippy" => {
                self.require_rust_workspace()?;
                let result = self.processes.run_cargo(
                    self.workspace.root(),
                    &[
                        "clippy",
                        "--workspace",
                        "--all-targets",
                        "--message-format=json",
                        "--",
                        "-D",
                        "warnings",
                    ],
                )?;
                Ok(serde_json::to_value(result).map_err(|e| e.to_string())?)
            }
            "build.certify" => {
                self.require_rust_workspace()?;
                let mut stages = Vec::<Value>::new();
                let mut success = true;

                let fmt = self.processes.run_capture(
                    self.workspace.root(),
                    "cargo",
                    &["fmt", "--all", "--", "--check"],
                    false,
                )?;
                success &= fmt.success;
                stages.push(json!({"name":"fmt_check","result":fmt}));

                if success {
                    let check = self.processes.run_cargo(
                        self.workspace.root(),
                        &["check", "--workspace", "--message-format=json"],
                    )?;
                    success &= check.success;
                    stages.push(json!({"name":"cargo_check","result":check}));
                }

                if success {
                    let tests = self.processes.run_capture(
                        self.workspace.root(),
                        "cargo",
                        &["test", "--workspace"],
                        false,
                    )?;
                    success &= tests.success;
                    stages.push(json!({"name":"cargo_test","result":tests}));
                }

                if success {
                    let clippy = self.processes.run_cargo(
                        self.workspace.root(),
                        &[
                            "clippy",
                            "--workspace",
                            "--all-targets",
                            "--message-format=json",
                            "--",
                            "-D",
                            "warnings",
                        ],
                    )?;
                    success &= clippy.success;
                    stages.push(json!({"name":"clippy","result":clippy}));
                }

                Ok(json!({"success": success, "stages": stages}))
            }
            "runtime.launch_foundry" => {
                let adapter = self
                    .open2d
                    .as_ref()
                    .ok_or_else(|| "Open2D adapter is not active for this workspace".to_string())?;
                let project = arg_string(&call.arguments, "project");
                let args = adapter.foundry_cargo_args(project.as_deref());
                let pid = self.processes.spawn_owned(
                    self.workspace.root(),
                    "Open2D Foundry",
                    "cargo",
                    &args,
                )?;
                self.session
                    .log("process", "launched Foundry", json!({"pid": pid}))?;
                Ok(json!({"pid": pid}))
            }
            "runtime.launch_ember" => {
                let adapter = self
                    .open2d
                    .as_ref()
                    .ok_or_else(|| "Open2D adapter is not active for this workspace".to_string())?;
                let level = arg_string(&call.arguments, "level");
                let args =
                    adapter.ember_cargo_args(&self.session.directory, level.as_deref());
                let pid = self.processes.spawn_owned(
                    self.workspace.root(),
                    "Open2D Ember",
                    "cargo",
                    &args,
                )?;
                self.session
                    .log("process", "launched Ember", json!({"pid": pid}))?;
                Ok(json!({"pid": pid, "session_dir": self.session.directory.clone()}))
            }
            "runtime.status" => {
                let statuses = self.processes.statuses();
                let snapshot = read_snapshot(&self.session.directory).ok();
                Ok(json!({"processes": statuses, "runtime": snapshot}))
            }
            "runtime.stop" => {
                let pid = required_u64(&call.arguments, "pid")? as u32;
                Ok(json!({"stopped": self.processes.stop(pid)?}))
            }
            "capture.window" => {
                let pid = required_u64(&call.arguments, "pid")? as u32;
                let relative = arg_string(&call.arguments, "output").map(PathBuf::from).unwrap_or_else(|| {
                    self.session
                        .directory
                        .strip_prefix(self.workspace.root())
                        .unwrap_or(self.session.directory.as_path())
                        .join("captures")
                        .join(format!("window-{pid}.png"))
                });
                let capture = self.capture.capture_process_window(pid, &relative)?;
                self.session.log("capture", "captured process window", json!({"pid": pid, "path": capture.path}))?;
                Ok(serde_json::to_value(capture).map_err(|e| e.to_string())?)
            }
            "vision.inspect" => {
                let relative = required_string(&call.arguments, "path")?;
                let prompt = arg_string(&call.arguments, "prompt").unwrap_or_else(|| {
                    "Inspect this Open2D editor/game screenshot. Identify rendering, layout, missing-content, clipping, alignment, and obvious runtime regressions. Return concise structured findings.".into()
                });
                let model = arg_string(&call.arguments, "model");
                let provider = self.vision_provider.as_ref().ok_or_else(|| "no Cortex vision provider is configured".to_string())?;
                let absolute = self.workspace.resolve(relative).map_err(|e| e.to_string())?;
                let image = self.capture.load_png_input(&absolute)?;
                let findings = provider.inspect(&image, &prompt, model.as_deref()).map_err(|e| e.to_string())?;
                Ok(json!({"provider": provider.provider_id(), "findings": findings}))
            }
            "image.generate" => {
                let provider = self.image_provider.as_ref().ok_or_else(|| "no Cortex image provider is configured".to_string())?;
                let provider_id = provider.provider_id().to_string();
                let request = ImageGenerationRequest {
                    prompt: required_string(&call.arguments, "prompt")?.to_string(),
                    negative_prompt: arg_string(&call.arguments, "negative_prompt"),
                    model: arg_string(&call.arguments, "model"),
                    width: arg_u64(&call.arguments, "width").unwrap_or(512).clamp(16, 4096) as u32,
                    height: arg_u64(&call.arguments, "height").unwrap_or(512).clamp(16, 4096) as u32,
                    seed: arg_u64(&call.arguments, "seed"),
                    count: arg_u64(&call.arguments, "count").unwrap_or(1).clamp(1, 16) as u32,
                    workflow: arg_string(&call.arguments, "workflow"),
                    output_dir: generated_output_root_from_state(&self.workspace.cortex_state_dir()),
                    tags: call.arguments.get("tags").and_then(Value::as_array)
                        .map(|items| items.iter().filter_map(Value::as_str).map(str::to_string).collect())
                        .unwrap_or_default(),
                };
                let artifacts = provider.generate(&request).map_err(|e| e.to_string())?;
                let mut registered = Vec::new();
                for artifact in artifacts {
                    registered.push(self.image_catalog.register(artifact, &metadata_root_from_state(&self.workspace.cortex_state_dir()))?);
                }
                self.image_catalog.save(&catalog_path_from_state(&self.workspace.cortex_state_dir()))?;
                Ok(json!({"provider": provider_id, "artifacts": registered}))
            }
            "image.promote" => {
                let id = required_string(&call.arguments, "id")?;
                let destination = required_string(&call.arguments, "destination")?;
                self.transactions.checkpoint_path(destination).map_err(|e| e.to_string())?;
                let path = self.image_catalog.promote(id, self.workspace.root(), Path::new(destination))?;
                self.image_catalog.save(&catalog_path_from_state(&self.workspace.cortex_state_dir()))?;
                Ok(json!({"promoted_to": path}))
            }
            "image.reject" => {
                let id = required_string(&call.arguments, "id")?;
                self.image_catalog.set_status(id, ImageArtifactStatus::Rejected)?;
                self.image_catalog.save(&catalog_path_from_state(&self.workspace.cortex_state_dir()))?;
                Ok(json!({"rejected": true}))
            }
            "image.archive" => {
                let id = required_string(&call.arguments, "id")?;
                self.image_catalog.set_status(id, ImageArtifactStatus::Archived)?;
                self.image_catalog.save(&catalog_path_from_state(&self.workspace.cortex_state_dir()))?;
                Ok(json!({"archived": true}))
            }
            "git.status" => {
                let git = self.git.as_ref().ok_or_else(|| "Git adapter is not active for this workspace".to_string())?;
                Ok(json!(git.status()?))
            }
            "git.diff" => {
                let git = self.git.as_ref().ok_or_else(|| "Git adapter is not active for this workspace".to_string())?;
                let paths = call.arguments.get("paths").and_then(Value::as_array).map(|items| items.iter().filter_map(Value::as_str).map(PathBuf::from).collect::<Vec<_>>()).unwrap_or_default();
                let staged = call.arguments.get("staged").and_then(Value::as_bool).unwrap_or(false);
                Ok(json!({"diff":git.diff(&paths, staged)?}))
            }
            "git.log" => {
                let git = self.git.as_ref().ok_or_else(|| "Git adapter is not active for this workspace".to_string())?;
                let limit = arg_u64(&call.arguments,"limit").unwrap_or(20).clamp(1,200) as usize;
                Ok(json!({"commits":git.log(limit)?}))
            }
            "vault.status" => Ok(json!(self.vault.status())),
            "vault.rebuild" | "memory.rebuild" => {
                let files = self.workspace.list_files("", 20_000).map_err(|e| e.to_string())?;
                self.vault = Vault::build_lexical(self.workspace.root(), &files, 512 * 1024);
                let path = self
                    .workspace
                    .cortex_state_dir()
                    .join("vault")
                    .join("vault.json");
                self.vault.save(&path)?;
                Ok(json!({"status": self.vault.status(), "path": path}))
            }
            "vault.search" | "memory.search" => {
                let query = required_string(&call.arguments, "query")?;
                let limit = arg_u64(&call.arguments, "limit").unwrap_or(8).clamp(1, 50) as usize;
                let hits = self
                    .vault
                    .search(query, limit, self.embedding_provider.as_deref())?;
                Ok(json!({"hits": hits}))
            }
            "plugins.list" => Ok(json!({
                "plugins": PluginRegistry::discover(
                    self.workspace.root(),
                    &self.workspace.cortex_state_dir()
                )?
            })),
            "permissions.status" => Ok(json!(&self.permissions)),
            "vscode.workspace_info" => self.call_vscode("vscode.workspace_info", json!({})),
            "vscode.open_file" => {
                let path = required_string(&call.arguments, "path")?;
                let line = arg_u64(&call.arguments, "line").unwrap_or(1);
                match self.call_vscode("vscode.open_file", json!({"path": path, "line": line})) {
                    Ok(value) => Ok(value),
                    Err(_) => {
                        let absolute = self.workspace.resolve(path).map_err(|e| e.to_string())?;
                        let target = format!("{}:{line}", absolute.display());
                        let result = self.processes.run_capture(self.workspace.root(), "code", &["-g", &target], false)?;
                        Ok(serde_json::to_value(result).map_err(|e| e.to_string())?)
                    }
                }
            }
            "vscode.get_diagnostics" => self.call_vscode("vscode.get_diagnostics", json!({})),
            "vscode.apply_workspace_edit" => {
                let edits = call.arguments.get("edits").cloned().ok_or_else(|| "missing edits argument".to_string())?;
                let items = edits.as_array().ok_or_else(|| "edits must be an array".to_string())?;
                for item in items {
                    let path = item.get("path").and_then(Value::as_str).ok_or_else(|| "each VS Code edit requires path".to_string())?;
                    self.transactions.checkpoint_path(path).map_err(|e| e.to_string())?;
                }
                self.call_vscode("vscode.apply_workspace_edit", json!({"edits": edits}))
            }
            "vscode.save_all" => self.call_vscode("vscode.save_all", json!({})),
            other => Err(format!("unknown Cortex tool: {other}")),
        }
    }
}

impl ToolExecutor for ToolBroker {
    fn definitions(&self) -> Vec<ToolDefinition> { definitions() }

    fn execute(&mut self, call: &ToolCall) -> ToolResultInput {
        match self.execute_inner(call) {
            Ok(output) => ToolResultInput { call_id: call.call_id.clone(), output, is_error: false },
            Err(error) => ToolResultInput { call_id: call.call_id.clone(), output: json!({"error": error}), is_error: true },
        }
    }
}

pub fn definitions() -> Vec<ToolDefinition> {
    vec![
        tool("workspace.status", "Read generic workspace detection, state, adapters and source authority status.", false, json!({"type":"object","properties":{}})),
        tool("project.status", "Compatibility alias for workspace.status.", false, json!({"type":"object","properties":{}})),
        tool("source.list", "List files under a safe workspace-relative path.", false, json!({"type":"object","properties":{"path":{"type":"string"},"max_files":{"type":"integer"}}})),
        tool("source.read", "Read a UTF-8 source/config/document file from the active workspace.", false, json!({"type":"object","properties":{"path":{"type":"string"},"max_bytes":{"type":"integer"}},"required":["path"]})),
        tool("source.search", "Search textual workspace files for an exact string.", false, json!({"type":"object","properties":{"query":{"type":"string"},"roots":{"type":"array","items":{"type":"string"}},"max_hits":{"type":"integer"}},"required":["query"]})),
        tool("source.transaction_status", "Read the active durable Cortex source transaction, if any.", false, json!({"type":"object","properties":{}})),
        tool("source.transaction_files", "List files touched or created by the active Cortex source transaction.", false, json!({"type":"object","properties":{}})),
        tool("source.checkpoint", "Checkpoint one project-relative path into the active transaction before an external edit.", true, json!({"type":"object","properties":{"path":{"type":"string"}},"required":["path"]})),
        tool("source.begin_transaction", "Begin a reversible durable Cortex source-edit transaction.", true, json!({"type":"object","properties":{"label":{"type":"string"}}})),
        tool("source.write_text", "Write an entire text file inside an active transaction.", true, json!({"type":"object","properties":{"path":{"type":"string"},"content":{"type":"string"}},"required":["path","content"]})),
        tool("source.replace_text", "Guarded exact source replacement inside an active transaction.", true, json!({"type":"object","properties":{"path":{"type":"string"},"old":{"type":"string"},"new":{"type":"string"},"expected_occurrences":{"type":"integer"}},"required":["path","old","new"]})),
        tool("source.commit", "Commit the active Cortex transaction.", true, json!({"type":"object","properties":{}})),
        tool("source.rollback", "Roll back the active Cortex transaction.", true, json!({"type":"object","properties":{}})),
        tool("build.cargo_fmt_check", "Verify rustfmt formatting across the active Rust workspace.", false, json!({"type":"object","properties":{}})),
        tool("build.cargo_check", "Run cargo check for the active Rust workspace and return structured compiler diagnostics.", false, json!({"type":"object","properties":{}})),
        tool("build.cargo_test", "Compile all Rust workspace tests and return structured diagnostics without running tests.", false, json!({"type":"object","properties":{}})),
        tool("build.cargo_test_run", "Run all active Rust workspace tests.", false, json!({"type":"object","properties":{}})),
        tool("build.clippy", "Run Clippy across the active Rust workspace with warnings denied and return structured diagnostics.", false, json!({"type":"object","properties":{}})),
        tool("build.certify", "Run the CLI certification build gate: fmt-check, cargo check, workspace tests and Clippy with warnings denied.", false, json!({"type":"object","properties":{}})),
        tool("runtime.launch_foundry", "Launch an owned Foundry development process.", true, json!({"type":"object","properties":{"project":{"type":"string"}}})),
        tool("runtime.launch_ember", "Launch an owned Ember development process.", true, json!({"type":"object","properties":{"level":{"type":"string"}}})),
        tool("runtime.status", "Read owned process and Ember runtime state.", false, json!({"type":"object","properties":{}})),
        tool("runtime.stop", "Stop a process owned by the current Cortex session.", true, json!({"type":"object","properties":{"pid":{"type":"integer"}},"required":["pid"]})),
        tool("capture.window", "Capture a Windows application window owned by a known process.", false, json!({"type":"object","properties":{"pid":{"type":"integer"},"output":{"type":"string"}},"required":["pid"]})),
        tool("vision.inspect", "Inspect a workspace PNG screenshot using the configured vision model.", false, json!({"type":"object","properties":{"path":{"type":"string"},"prompt":{"type":"string"},"model":{"type":"string"}},"required":["path"]})),
        tool("image.generate", "Generate managed Cortex image artifacts through the configured image provider.", true, json!({"type":"object","properties":{"prompt":{"type":"string"},"negative_prompt":{"type":"string"},"model":{"type":"string"},"width":{"type":"integer"},"height":{"type":"integer"},"seed":{"type":"integer"},"count":{"type":"integer"},"workflow":{"type":"string"},"tags":{"type":"array","items":{"type":"string"}}},"required":["prompt"]})),
        tool("image.promote", "Promote a generated Cortex image artifact into project content.", true, json!({"type":"object","properties":{"id":{"type":"string"},"destination":{"type":"string"}},"required":["id","destination"]})),
        tool("image.reject", "Mark a generated image artifact as rejected.", true, json!({"type":"object","properties":{"id":{"type":"string"}},"required":["id"]})),
        tool("image.archive", "Archive a generated image artifact.", true, json!({"type":"object","properties":{"id":{"type":"string"}},"required":["id"]})),
        tool("git.status", "Read Git branch and working-tree status.", false, json!({"type":"object","properties":{}})),
        tool("git.diff", "Read Git working-tree or staged diff.", false, json!({"type":"object","properties":{"paths":{"type":"array","items":{"type":"string"}},"staged":{"type":"boolean"}}})),
        tool("git.log", "Read recent Git commit history.", false, json!({"type":"object","properties":{"limit":{"type":"integer"}}})),
        tool("vault.status", "Read Cortex Vault lexical/vector index status.", false, json!({"type":"object","properties":{}})),
        tool("vault.rebuild", "Rebuild Cortex Vault lexical source index.", false, json!({"type":"object","properties":{}})),
        tool("vault.search", "Retrieve hybrid lexical/vector context from Cortex Vault.", false, json!({"type":"object","properties":{"query":{"type":"string"},"limit":{"type":"integer"}},"required":["query"]})),
        tool("memory.rebuild", "Compatibility alias for vault.rebuild.", false, json!({"type":"object","properties":{}})),
        tool("memory.search", "Compatibility alias for vault.search.", false, json!({"type":"object","properties":{"query":{"type":"string"},"limit":{"type":"integer"}},"required":["query"]})),
        tool("plugins.list", "List built-in and workspace Cortex plugin manifests.", false, json!({"type":"object","properties":{}})),
        tool("permissions.status", "Read current Cortex permissions; agents cannot grant themselves access.", false, json!({"type":"object","properties":{}})),
        tool("vscode.workspace_info", "Read active VS Code workspace, file and selection context from the Cortex VS Code bridge.", false, json!({"type":"object","properties":{}})),
        tool("vscode.open_file", "Open and reveal a project source file in VS Code; falls back to the code CLI when bridge is unavailable.", false, json!({"type":"object","properties":{"path":{"type":"string"},"line":{"type":"integer"}},"required":["path"]})),
        tool("vscode.get_diagnostics", "Read current VS Code/rust-analyzer diagnostics for the active project.", false, json!({"type":"object","properties":{}})),
        tool("vscode.apply_workspace_edit", "Apply grouped project-relative text edits through VS Code WorkspaceEdit.", true, json!({"type":"object","properties":{"edits":{"type":"array"}},"required":["edits"]})),
        tool("vscode.save_all", "Save dirty VS Code workspace documents.", true, json!({"type":"object","properties":{}})),
    ]
}

fn tool(name: &str, description: &str, mutating: bool, parameters: Value) -> ToolDefinition {
    ToolDefinition { name: name.into(), description: description.into(), parameters, mutating }
}

fn required_string<'a>(value: &'a Value, key: &str) -> Result<&'a str, String> {
    value.get(key).and_then(Value::as_str).ok_or_else(|| format!("missing string argument: {key}"))
}
fn arg_string(value: &Value, key: &str) -> Option<String> { value.get(key).and_then(Value::as_str).map(str::to_string) }
fn arg_u64(value: &Value, key: &str) -> Option<u64> { value.get(key).and_then(Value::as_u64) }
fn required_u64(value: &Value, key: &str) -> Result<u64, String> {
    arg_u64(value, key).ok_or_else(|| format!("missing integer argument: {key}"))
}

fn unix_ms() -> u128 { SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_millis() }
