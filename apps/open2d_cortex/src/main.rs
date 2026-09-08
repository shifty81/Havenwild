use open2d_cortex_core::{AgentEngine, AgentMode, AgentSettings, AgentTurnResult};
use open2d_cortex_provider_comfyui::ComfyUiProvider;
use open2d_cortex_provider_lmstudio::LmStudioProvider;
use open2d_cortex_protocol::{
    ImageProvider, ModelRequest, RpcRequest, RpcResponse, TextProvider, ToolCall, ToolDefinition,
    ToolExecutor, VisionProvider,
};
use open2d_cortex_rpc::{default_address, RpcHandler, RpcServer};
use open2d_cortex_tools::ToolBroker;
use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};
use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::{
    atomic::{AtomicBool, Ordering},
    Arc,
};
use std::thread;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

type CortexEngine = AgentEngine<LmStudioProvider, ToolBroker>;

fn main() {
    if let Err(error) = run() {
        eprintln!("Open2D Cortex failed: {error}");
        std::process::exit(1);
    }
}

fn run() -> Result<(), String> {
    let args: Vec<String> = env::args().skip(1).collect();
    let project_root = find_project_root(env::current_dir().map_err(|e| e.to_string())?)?;
    let lm_url =
        env::var("OPEN2D_LMSTUDIO_URL").unwrap_or_else(|_| "http://127.0.0.1:1234/v1".into());
    let model_role = model_role_for_command(&args);
    let lm_model = configured_lm_model_for_role(&project_root, model_role);
    let lm_timeout = configured_lm_timeout();
    let lm = LmStudioProvider::with_timeout(lm_url, lm_model, lm_timeout);

    let vision_provider: Option<Box<dyn VisionProvider>> = Some(Box::new(lm.clone()));
    let image_provider: Option<Box<dyn ImageProvider>> = match env::var("OPEN2D_COMFYUI_WORKFLOW") {
        Ok(workflow) if !workflow.trim().is_empty() => {
            let url = env::var("OPEN2D_COMFYUI_URL")
                .unwrap_or_else(|_| "http://127.0.0.1:8188".into());
            Some(Box::new(ComfyUiProvider::new(url, workflow)))
        }
        _ => None,
    };

    let tools = ToolBroker::new(&project_root, image_provider, vision_provider)?;
    let mode = agent_mode_from_env();
    let settings = AgentSettings {
        mode,
        max_tool_iterations: configured_agent_iterations(),
        max_elapsed_seconds: configured_agent_deadline().as_secs(),
        ..AgentSettings::default()
    };
    let engine = AgentEngine::new(lm, tools, settings);
    let rpc_token = ensure_rpc_token(&project_root)?;
    let mut service = CortexService { engine, rpc_token };

    match args.first().map(String::as_str).unwrap_or("status") {
        "status" => {
            let call = ToolCall {
                call_id: "status".into(),
                name: "project.status".into(),
                arguments: json!({}),
            };
            let result = service.engine.tools_mut().execute(&call);
            println!(
                "{}",
                serde_json::to_string_pretty(&result.output).map_err(|e| e.to_string())?
            );
            eprintln!("Cortex provider: LM Studio");
            eprintln!(
                "Configured model: {}",
                configured_model_description(&project_root, model_role)
            );
            eprintln!("Inference timeout: {} seconds", lm_timeout.as_secs());
            eprintln!("Project-agent deadline: {} seconds", configured_agent_deadline().as_secs());
            eprintln!("Project-agent max iterations: {}", configured_agent_iterations());
        }
        "models" => {
            let selected = configured_lm_model_for_role(&project_root, model_role);
            let capabilities = service
                .engine
                .provider()
                .model_capabilities()
                .unwrap_or_default();
            for model in service
                .engine
                .provider()
                .list_models()
                .map_err(|e| e.to_string())?
            {
                let marker = if selected.as_deref() == Some(model.as_str()) {
                    "*"
                } else {
                    " "
                };
                let capability = capabilities.iter().find(|info| {
                    info.key == model
                        || info
                            .loaded_instance_ids
                            .iter()
                            .any(|loaded| loaded == &model)
                });
                let tool = match capability.and_then(|info| info.trained_for_tool_use) {
                    Some(true) => "tool=yes",
                    Some(false) => "tool=no",
                    None => "tool=?",
                };
                let vision = match capability.and_then(|info| info.vision) {
                    Some(true) => "vision=yes",
                    Some(false) => "vision=no",
                    None => "vision=?",
                };
                println!("{marker} {model}  [{tool}, {vision}]");
            }
            if selected.is_none() {
                println!();
                println!("No explicit model selected; Cortex will choose the first non-embedding text model.");
            }
        }
        "model" => {
            model_command(&project_root, service.engine.provider(), &args[1..])?;
        }
        "doctor" => {
            doctor_command(&project_root, &mut service, &args[1..])?;
        }
        "tools" => {
            tools_command(&mut service, &args[1..])?;
        }
        "tx" => {
            transaction_command(&mut service, &args[1..])?;
        }
        "build" => {
            build_command(&mut service, &args[1..])?;
        }
        "session" => {
            session_command(&project_root, &args[1..])?;
        }
        "logs" => {
            logs_command(&project_root, &args[1..])?;
        }
        "certify" => {
            certify_command(&project_root, &mut service, &args[1..])?;
        }
        "help" | "--help" | "-h" => {
            print_cli_help();
        }
        "chat" | "ask" => {
            let prompt = prompt_from_args(&args[1..]);
            if prompt.trim().is_empty() {
                return Err("usage: open2d_cortex chat <prompt> [--json|--jsonl]".into());
            }
            if args.first().map(String::as_str) == Some("ask") {
                eprintln!(
                    "Compatibility: `ask` now uses general chat mode. Use `inspect` for grounded project facts."
                );
            }

            let model = service
                .engine
                .provider()
                .resolve_model()
                .map_err(|e| e.to_string())?;
            let output = output_mode(&args);

            if output == OutputMode::Human {
                print_request_header(
                    "CHAT",
                    &model,
                    mode,
                    lm_timeout,
                    None,
                    "NONE (no project tools)",
                );
            }
            emit_event(output, "request_started", json!({
                "kind":"chat",
                "provider":"lmstudio",
                "model":model,
                "grounding":"none"
            }));
            let result = run_with_progress(
                "chat",
                lm_timeout,
                output,
                || service.engine.chat(&prompt),
            )?;
            match output {
                OutputMode::Human => {
                    println!("{}", result.text);
                    eprintln!("Grounding : N/A - chat mode");
                    eprintln!("Iterations: {}", result.iterations);
                }
                OutputMode::Json => println!("{}", serde_json::to_string_pretty(&json!({
                    "schema_version":1,
                    "mode":"chat",
                    "grounding":"none",
                    "model":model,
                    "text":result.text,
                    "iterations":result.iterations
                })).map_err(|e| e.to_string())?),
                OutputMode::Jsonl => emit_event(output, "agent_finished", json!({
                    "mode":"chat",
                    "grounding":"none",
                    "model":model,
                    "text":result.text,
                    "iterations":result.iterations
                })),
            }
        }
        "inspect" | "plan" | "apply" | "repair" => {
            let action = args.first().map(String::as_str).unwrap_or("inspect");
            let prompt = prompt_from_args(&args[1..]);
            if prompt.trim().is_empty() {
                return Err(format!("usage: open2d_cortex {action} <prompt> [--json|--jsonl]"));
            }
            project_agent_command(
                &mut service,
                action,
                &prompt,
                lm_timeout,
                output_mode(&args),
                args.iter().any(|arg| arg == "--reuse-transaction"),
            )?;
        }
        "tool" => {
            let name = args
                .get(1)
                .ok_or_else(|| "usage: open2d_cortex tool <name> [json-args]".to_string())?;
            let arguments = args
                .get(2)
                .map(|text| serde_json::from_str::<Value>(text).map_err(|e| e.to_string()))
                .transpose()?
                .unwrap_or_else(|| json!({}));
            let call = ToolCall {
                call_id: "cli-tool".into(),
                name: name.clone(),
                arguments,
            };
            let result = service.engine.tools_mut().execute(&call);
            println!(
                "{}",
                serde_json::to_string_pretty(&result.output).map_err(|e| e.to_string())?
            );
            if result.is_error {
                std::process::exit(2);
            }
        }
        "serve" => {
            let port = args
                .get(1)
                .map(|value| value.parse::<u16>())
                .transpose()
                .map_err(|e| e.to_string())?
                .unwrap_or(7337);
            let server = RpcServer::bind(default_address(port))?;
            println!("Open2D Cortex RPC listening at {}", server.local_addr()?);
            println!("Project: {}", project_root.display());
            println!(
                "LM Studio model: {}",
                service
                    .engine
                    .provider()
                    .resolve_model()
                    .unwrap_or_else(|_| "<unresolved>".into())
            );
            server.serve(&mut service)?;
        }
        other => return Err(format!("unknown Cortex command: {other}; run `open2d_cortex help`")),
    }
    Ok(())
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum OutputMode {
    Human,
    Json,
    Jsonl,
}

fn output_mode(args: &[String]) -> OutputMode {
    if args.iter().any(|arg| arg == "--jsonl") {
        OutputMode::Jsonl
    } else if args.iter().any(|arg| arg == "--json") {
        OutputMode::Json
    } else {
        OutputMode::Human
    }
}

fn prompt_from_args(args: &[String]) -> String {
    args.iter()
        .filter(|arg| {
            !matches!(arg.as_str(), "--json" | "--jsonl" | "--reuse-transaction")
        })
        .cloned()
        .collect::<Vec<_>>()
        .join(" ")
}

fn emit_event(mode: OutputMode, event: &str, data: Value) {
    if mode == OutputMode::Jsonl {
        println!("{}", json!({"event":event,"data":data}));
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
enum ModelRole {
    Default,
    Chat,
    Tool,
    Vision,
    Embedding,
}

impl ModelRole {
    fn as_str(self) -> &'static str {
        match self {
            Self::Default => "default",
            Self::Chat => "chat",
            Self::Tool => "tool",
            Self::Vision => "vision",
            Self::Embedding => "embedding",
        }
    }

    fn parse(value: &str) -> Option<Self> {
        match value.to_ascii_lowercase().as_str() {
            "default" => Some(Self::Default),
            "chat" => Some(Self::Chat),
            "tool" | "tools" | "coding" => Some(Self::Tool),
            "vision" => Some(Self::Vision),
            "embedding" | "embeddings" => Some(Self::Embedding),
            _ => None,
        }
    }

    fn env_key(self) -> &'static str {
        match self {
            Self::Default => "OPEN2D_LMSTUDIO_MODEL",
            Self::Chat => "OPEN2D_LMSTUDIO_MODEL_CHAT",
            Self::Tool => "OPEN2D_LMSTUDIO_MODEL_TOOL",
            Self::Vision => "OPEN2D_LMSTUDIO_MODEL_VISION",
            Self::Embedding => "OPEN2D_LMSTUDIO_MODEL_EMBEDDING",
        }
    }

    fn all() -> [Self; 5] {
        [
            Self::Default,
            Self::Chat,
            Self::Tool,
            Self::Vision,
            Self::Embedding,
        ]
    }
}

fn model_role_for_command(args: &[String]) -> ModelRole {
    match args.first().map(String::as_str).unwrap_or("status") {
        "chat" | "ask" => ModelRole::Chat,
        "inspect" | "plan" | "apply" | "repair" | "doctor" | "tools" | "tx" | "build" | "certify" | "serve" => ModelRole::Tool,
        "tool"
            if args
                .get(1)
                .map(|name| name == "vision.inspect")
                .unwrap_or(false) =>
        {
            ModelRole::Vision
        }
        "tool" => ModelRole::Tool,
        _ => ModelRole::Default,
    }
}

fn model_command(
    project_root: &Path,
    provider: &LmStudioProvider,
    args: &[String],
) -> Result<(), String> {
    match args.first().map(String::as_str).unwrap_or("current") {
        "current" => {
            let role = args
                .get(1)
                .and_then(|value| ModelRole::parse(value))
                .unwrap_or(ModelRole::Default);
            println!("{}", configured_model_description(project_root, role));
        }
        "roles" => {
            for role in ModelRole::all() {
                println!(
                    "{:<10} {}",
                    role.as_str(),
                    configured_model_description(project_root, role)
                );
            }
        }
        "set" => {
            let (role, model_index) = match args.get(1).and_then(|value| ModelRole::parse(value)) {
                Some(role) => (role, 2),
                None => (ModelRole::Default, 1),
            };
            let model = args.get(model_index).ok_or_else(|| {
                "usage: open2d_cortex model set [default|chat|tool|vision|embedding] <model-id>"
                    .to_string()
            })?;
            let models = provider.list_models().map_err(|e| e.to_string())?;
            if !models.iter().any(|candidate| candidate == model) {
                return Err(format!(
                    "LM Studio model is not currently visible: {model}\nAvailable models:\n  {}",
                    models.join("\n  ")
                ));
            }
            let path = model_config_path(project_root, role);
            if let Some(parent) = path.parent() {
                fs::create_dir_all(parent).map_err(|e| e.to_string())?;
            }
            fs::write(&path, model.as_bytes()).map_err(|e| e.to_string())?;
            println!("Selected LM Studio {} model: {model}", role.as_str());
            println!("Stored at: {}", path.display());
        }
        "clear" => {
            let role = args
                .get(1)
                .and_then(|value| ModelRole::parse(value))
                .unwrap_or(ModelRole::Default);
            let path = model_config_path(project_root, role);
            if path.exists() {
                fs::remove_file(&path).map_err(|e| e.to_string())?;
            }
            println!("Cleared project LM Studio {} model selection.", role.as_str());
        }
        other => {
            return Err(format!(
                "unknown model command: {other}; use current [role], roles, set [role] <model-id>, or clear [role]"
            ));
        }
    }
    Ok(())
}

fn configured_lm_model_for_role(project_root: &Path, role: ModelRole) -> Option<String> {
    configured_role_value(project_root, role).or_else(|| {
        if role == ModelRole::Default {
            None
        } else {
            configured_role_value(project_root, ModelRole::Default)
        }
    })
}

fn configured_role_value(project_root: &Path, role: ModelRole) -> Option<String> {
    env::var(role.env_key())
        .ok()
        .filter(|value| !value.trim().is_empty())
        .or_else(|| {
            fs::read_to_string(model_config_path(project_root, role))
                .ok()
                .map(|value| value.trim().to_string())
                .filter(|value| !value.is_empty())
        })
}

fn configured_model_description(project_root: &Path, role: ModelRole) -> String {
    if let Ok(value) = env::var(role.env_key()) {
        if !value.trim().is_empty() {
            return format!(
                "{} ({} / {} role)",
                value.trim(),
                role.env_key(),
                role.as_str()
            );
        }
    }

    let path = model_config_path(project_root, role);
    if let Ok(value) = fs::read_to_string(&path) {
        if !value.trim().is_empty() {
            return format!(
                "{} (project {} role)",
                value.trim(),
                role.as_str()
            );
        }
    }

    if role != ModelRole::Default {
        if let Some(fallback) = configured_role_value(project_root, ModelRole::Default) {
            return format!("{fallback} (fallback from default role)");
        }
    }

    "<automatic: first non-embedding text model>".into()
}

fn model_config_path(project_root: &Path, role: ModelRole) -> PathBuf {
    let file_name = match role {
        ModelRole::Default => "lmstudio-model.txt".to_string(),
        _ => format!("lmstudio-model-{}.txt", role.as_str()),
    };
    project_root.join(".open2d").join("cortex").join(file_name)
}

fn doctor_command(
    project_root: &Path,
    service: &mut CortexService,
    args: &[String],
) -> Result<(), String> {
    let full = args.iter().any(|arg| arg.eq_ignore_ascii_case("full") || arg == "--full");
    let json_mode = args.iter().any(|arg| arg == "--json");
    let mut checks = Vec::<Value>::new();

    doctor_check(
        &mut checks,
        "workspace",
        project_root.join("Cargo.toml").is_file(),
        json!({"root": project_root}),
    );

    let models = service.engine.provider().list_models();
    doctor_check(
        &mut checks,
        "lmstudio",
        models.is_ok(),
        match &models {
            Ok(values) => json!({"models_visible": values.len()}),
            Err(error) => json!({"error": error.to_string()}),
        },
    );

    let resolved_model = service.engine.provider().resolve_model();
    doctor_check(
        &mut checks,
        "model_resolution",
        resolved_model.is_ok(),
        match &resolved_model {
            Ok(model) => json!({"model": model}),
            Err(error) => json!({"error": error.to_string()}),
        },
    );

    if let Ok(model) = &resolved_model {
        let capability = service
            .engine
            .provider()
            .capability_for_model(model)
            .ok()
            .flatten();
        doctor_check(
            &mut checks,
            "tool_model_capability",
            !matches!(
                capability.as_ref().and_then(|info| info.trained_for_tool_use),
                Some(false)
            ),
            json!({
                "model": model,
                "trained_for_tool_use": capability.as_ref().and_then(|info| info.trained_for_tool_use),
                "vision": capability.as_ref().and_then(|info| info.vision)
            }),
        );
    }

    let definitions = service.engine.tools().definitions();
    let certification = certify_tool_definitions(&definitions);
    doctor_check(
        &mut checks,
        "tool_registry",
        certification
            .get("ok")
            .and_then(Value::as_bool)
            .unwrap_or(false),
        certification,
    );

    let project_status = service.engine.tools_mut().execute(&ToolCall {
        call_id: "doctor-project-status".into(),
        name: "project.status".into(),
        arguments: json!({}),
    });
    doctor_check(
        &mut checks,
        "project_status_tool",
        !project_status.is_error,
        project_status.output,
    );

    let token_path = project_root.join(".open2d").join("cortex").join("rpc.token");
    let token_ok = fs::read_to_string(&token_path)
        .ok()
        .map(|token| token.trim().len() >= 24)
        .unwrap_or(false);
    doctor_check(
        &mut checks,
        "rpc_token",
        token_ok,
        json!({"path": token_path}),
    );

    if full {
        let tool_smoke = match resolved_model {
            Ok(model) => run_provider_tool_smoke(service.engine.provider(), &model, &definitions),
            Err(error) => Err(error.to_string()),
        };
        doctor_check(
            &mut checks,
            "structured_tool_call_smoke",
            tool_smoke.is_ok(),
            match tool_smoke {
                Ok(value) => value,
                Err(error) => json!({"error": error}),
            },
        );
    }

    let ready = checks
        .iter()
        .all(|check| check.get("ok").and_then(Value::as_bool).unwrap_or(false));
    let report = json!({
        "schema_version": 1,
        "command": if full { "doctor_full" } else { "doctor_quick" },
        "ready": ready,
        "checks": checks
    });

    if json_mode {
        println!(
            "{}",
            serde_json::to_string_pretty(&report).map_err(|e| e.to_string())?
        );
    } else {
        println!("OPEN2D CORTEX DOCTOR");
        println!("Mode: {}", if full { "FULL" } else { "QUICK" });
        for check in report
            .get("checks")
            .and_then(Value::as_array)
            .into_iter()
            .flatten()
        {
            let ok = check.get("ok").and_then(Value::as_bool).unwrap_or(false);
            let name = check.get("name").and_then(Value::as_str).unwrap_or("check");
            println!("[{}] {name}", if ok { "PASS" } else { "FAIL" });
        }
        println!();
        println!(
            "Open2D Cortex: {}",
            if ready { "READY" } else { "NOT READY" }
        );
    }

    if ready {
        Ok(())
    } else {
        Err("Cortex doctor found one or more required failures".into())
    }
}

fn doctor_check(checks: &mut Vec<Value>, name: &str, ok: bool, details: Value) {
    checks.push(json!({
        "name": name,
        "ok": ok,
        "details": details
    }));
}

fn run_provider_tool_smoke(
    provider: &LmStudioProvider,
    model: &str,
    definitions: &[ToolDefinition],
) -> Result<Value, String> {
    let project_status = definitions
        .iter()
        .find(|tool| tool.name == "project.status")
        .cloned()
        .ok_or_else(|| "project.status tool definition is missing".to_string())?;

    let mut request = ModelRequest::user(
        "For this certification check, call the project status function once. Do not answer from memory.",
    );
    request.model = Some(model.to_string());
    request.instructions = Some(
        "This is an Open2D Cortex structured-tool certification. Emit the required tool call."
            .into(),
    );
    request.tools = vec![project_status];

    let response = provider.respond(&request).map_err(|e| e.to_string())?;
    let called = response
        .tool_calls
        .iter()
        .any(|call| call.name == "project.status");
    if !called {
        return Err(format!(
            "model returned no project.status structured tool call; response text preview: {}",
            response.output_text.chars().take(240).collect::<String>()
        ));
    }

    Ok(json!({
        "model": model,
        "response_id": response.id,
        "tool_calls": response.tool_calls
    }))
}

fn tools_command(service: &mut CortexService, args: &[String]) -> Result<(), String> {
    let command = args.first().map(String::as_str).unwrap_or("list");
    let json_mode = args.iter().any(|arg| arg == "--json");
    let definitions = service.engine.tools().definitions();

    match command {
        "list" => {
            if json_mode {
                println!(
                    "{}",
                    serde_json::to_string_pretty(&definitions).map_err(|e| e.to_string())?
                );
            } else {
                for definition in &definitions {
                    println!(
                        "{:<34} {:<7} {}",
                        definition.name,
                        if definition.mutating { "WRITE" } else { "READ" },
                        definition.description
                    );
                }
                println!("{} tool(s)", definitions.len());
            }
        }
        "describe" => {
            let name = args
                .get(1)
                .ok_or_else(|| "usage: open2d_cortex tools describe <name> [--json]".to_string())?;
            let definition = definitions
                .iter()
                .find(|definition| &definition.name == name)
                .ok_or_else(|| format!("unknown Cortex tool: {name}"))?;
            if json_mode {
                println!(
                    "{}",
                    serde_json::to_string_pretty(definition).map_err(|e| e.to_string())?
                );
            } else {
                println!("Name      : {}", definition.name);
                println!(
                    "Authority : {}",
                    if definition.mutating { "MUTATING" } else { "READ-ONLY" }
                );
                println!("Wire name : {}", provider_safe_tool_name(&definition.name));
                println!("Purpose   : {}", definition.description);
                println!(
                    "Schema    : {}",
                    serde_json::to_string_pretty(&definition.parameters)
                        .map_err(|e| e.to_string())?
                );
            }
        }
        "certify" => {
            let report = certify_tool_definitions(&definitions);
            let ok = report.get("ok").and_then(Value::as_bool).unwrap_or(false);
            if json_mode {
                println!(
                    "{}",
                    serde_json::to_string_pretty(&report).map_err(|e| e.to_string())?
                );
            } else {
                println!("OPEN2D CORTEX TOOL CERTIFICATION");
                println!("Tools : {}", definitions.len());
                println!("Result: {}", if ok { "PASS" } else { "FAIL" });
                if let Some(issues) = report.get("issues").and_then(Value::as_array) {
                    for issue in issues {
                        if let Some(issue) = issue.as_str() {
                            println!(" - {issue}");
                        }
                    }
                }
            }
            if !ok {
                return Err("tool certification failed".into());
            }
        }
        "test" => {
            let name = args
                .get(1)
                .ok_or_else(|| "usage: open2d_cortex tools test <name> [json-args] [--allow-mutation]".to_string())?;
            let definition = definitions
                .iter()
                .find(|definition| &definition.name == name)
                .ok_or_else(|| format!("unknown Cortex tool: {name}"))?;
            let allow_mutation = args.iter().any(|arg| arg == "--allow-mutation");
            if definition.mutating && !allow_mutation {
                return Err(format!(
                    "tool `{name}` is mutating; rerun with --allow-mutation only when intentional"
                ));
            }
            let arguments = args
                .iter()
                .skip(2)
                .find(|arg| !arg.starts_with("--"))
                .map(|text| serde_json::from_str::<Value>(text).map_err(|e| e.to_string()))
                .transpose()?
                .unwrap_or_else(|| json!({}));
            let result = service.engine.tools_mut().execute(&ToolCall {
                call_id: format!("cli-tool-test-{}", unix_ms()),
                name: name.clone(),
                arguments,
            });
            println!(
                "{}",
                serde_json::to_string_pretty(&json!({
                    "tool": name,
                    "is_error": result.is_error,
                    "output": result.output
                }))
                .map_err(|e| e.to_string())?
            );
            if result.is_error {
                return Err(format!("tool test failed: {name}"));
            }
        }
        "test-all" => {
            let safe_smoke = ["project.status", "source.transaction_status", "runtime.status"];
            let mut results = Vec::<Value>::new();
            let mut failed = false;
            for name in safe_smoke {
                let result = service.engine.tools_mut().execute(&ToolCall {
                    call_id: format!("cli-tool-smoke-{name}"),
                    name: name.into(),
                    arguments: json!({}),
                });
                failed |= result.is_error;
                results.push(json!({
                    "tool": name,
                    "ok": !result.is_error,
                    "output": result.output
                }));
            }
            println!(
                "{}",
                serde_json::to_string_pretty(&json!({"results": results}))
                    .map_err(|e| e.to_string())?
            );
            if failed {
                return Err("one or more safe tool smoke tests failed".into());
            }
        }
        other => {
            return Err(format!(
                "unknown tools command: {other}; use list, describe, certify, test, or test-all"
            ));
        }
    }

    Ok(())
}

fn certify_tool_definitions(definitions: &[ToolDefinition]) -> Value {
    let mut issues = Vec::<String>::new();
    let mut canonical = BTreeSet::<String>::new();
    let mut wire = BTreeMap::<String, String>::new();

    for definition in definitions {
        if definition.name.trim().is_empty() {
            issues.push("tool with empty canonical name".into());
        }
        if !canonical.insert(definition.name.clone()) {
            issues.push(format!("duplicate canonical tool name: {}", definition.name));
        }
        if definition.description.trim().is_empty() {
            issues.push(format!("tool has empty description: {}", definition.name));
        }
        if !definition.parameters.is_object() {
            issues.push(format!(
                "tool parameters are not a JSON object schema: {}",
                definition.name
            ));
        }

        let wire_name = provider_safe_tool_name(&definition.name);
        if wire_name.is_empty() || wire_name.len() > 64 {
            issues.push(format!(
                "provider-safe tool name has invalid length: {} -> {}",
                definition.name, wire_name
            ));
        }
        if let Some(existing) = wire.insert(wire_name.clone(), definition.name.clone()) {
            if existing != definition.name {
                issues.push(format!(
                    "provider-safe tool-name collision: {existing} and {} -> {wire_name}",
                    definition.name
                ));
            }
        }
    }

    json!({
        "ok": issues.is_empty(),
        "tool_count": definitions.len(),
        "issues": issues
    })
}

fn provider_safe_tool_name(name: &str) -> String {
    name.chars()
        .map(|ch| {
            if ch.is_ascii_alphanumeric() || matches!(ch, '_' | '-') {
                ch
            } else {
                '_'
            }
        })
        .take(64)
        .collect()
}

fn transaction_command(service: &mut CortexService, args: &[String]) -> Result<(), String> {
    let command = args.first().map(String::as_str).unwrap_or("status");
    let (tool_name, arguments) = match command {
        "status" => ("source.transaction_status", json!({})),
        "files" => ("source.transaction_files", json!({})),
        "begin" => {
            let label = if args.len() > 1 {
                args[1..].join(" ")
            } else {
                "cli-edit".into()
            };
            ("source.begin_transaction", json!({"label": label}))
        }
        "checkpoint" => {
            let path = args
                .get(1)
                .ok_or_else(|| "usage: open2d_cortex tx checkpoint <project-relative-path>".to_string())?;
            ("source.checkpoint", json!({"path": path}))
        }
        "commit" => {
            if !args.iter().any(|arg| arg == "--force") {
                let verification = execute_named_tool(
                    service,
                    "build.cargo_check",
                    json!({}),
                    "tx-commit-check",
                );
                if !tool_result_success(&verification) {
                    println!(
                        "{}",
                        serde_json::to_string_pretty(&verification.output)
                            .map_err(|e| e.to_string())?
                    );
                    return Err(
                        "transaction commit blocked because cargo check failed; repair, rollback, or use tx commit --force intentionally"
                            .into(),
                    );
                }
            }
            ("source.commit", json!({}))
        }
        "rollback" => ("source.rollback", json!({})),
        other => {
            return Err(format!(
                "unknown transaction command: {other}; use status, files, begin, checkpoint, commit, or rollback"
            ));
        }
    };

    let result = service.engine.tools_mut().execute(&ToolCall {
        call_id: format!("cli-tx-{}", unix_ms()),
        name: tool_name.into(),
        arguments,
    });

    println!(
        "{}",
        serde_json::to_string_pretty(&result.output).map_err(|e| e.to_string())?
    );
    if result.is_error {
        Err(format!("transaction command failed: {command}"))
    } else {
        Ok(())
    }
}

fn project_agent_command(
    service: &mut CortexService,
    action: &str,
    prompt: &str,
    lm_timeout: Duration,
    output: OutputMode,
    reuse_transaction: bool,
) -> Result<(), String> {
    let model = service
        .engine
        .provider()
        .resolve_model()
        .map_err(|e| e.to_string())?;
    let capability = service
        .engine
        .provider()
        .capability_for_model(&model)
        .ok()
        .flatten();

    if matches!(
        capability.as_ref().and_then(|info| info.trained_for_tool_use),
        Some(false)
    ) {
        return Err(format!(
            "Selected LM Studio model `{model}` reports tool=no. `{action}` requires structured tool use. Select a tool-capable model for the Cortex tool role."
        ));
    }

    let mutating = matches!(action, "apply" | "repair");
    let mode = if mutating {
        AgentMode::WorkspaceAutonomy
    } else {
        AgentMode::Observe
    };
    service.engine.set_mode(mode);

    let tx_id = if mutating {
        Some(ensure_active_transaction(service, action, reuse_transaction)?)
    } else {
        None
    };

    let effective_prompt = match action {
        "plan" => format!(
            "Read-only planning mode. Inspect the current project using Open2D tools. Do not mutate files. Produce a concrete implementation plan with files, validation steps and risks.\n\nUser request: {prompt}"
        ),
        "apply" => format!(
            "An active durable Cortex transaction is already open. Do not begin another transaction and do not commit or roll it back. Apply the requested bounded changes using Open2D source tools, then run build.cargo_check before finishing. Leave the transaction active for human review.\n\nUser request: {prompt}"
        ),
        "repair" => format!(
            "An active durable Cortex transaction is already open. Do not begin another transaction and do not commit or roll it back. Diagnose the requested problem from current source/build evidence, make bounded repairs, and use build tools until cargo check is green. Leave the transaction active for human review.\n\nRepair request: {prompt}"
        ),
        _ => prompt.to_string(),
    };

    let tool_status = match capability
        .as_ref()
        .and_then(|info| info.trained_for_tool_use)
    {
        Some(true) => "trained",
        Some(false) => "not trained",
        None => "unknown/parser-dependent",
    };

    if output == OutputMode::Human {
        print_request_header(
            &format!("PROJECT {}", action.to_ascii_uppercase()),
            &model,
            mode,
            lm_timeout,
            Some(service.engine.settings().max_elapsed_seconds),
            "REQUIRED",
        );
        eprintln!("Tool use  : {tool_status}");
        if let Some(id) = &tx_id {
            eprintln!("Transaction: {id} (left active for review)");
        }
    }
    emit_event(output, "request_started", json!({
        "kind":action,
        "provider":"lmstudio",
        "model":model,
        "grounding":"required",
        "transaction_id":tx_id
    }));

    let agent_limit = Duration::from_secs(service.engine.settings().max_elapsed_seconds);
    let result = run_with_progress(
        "project agent",
        agent_limit,
        output,
        || service.engine.run(&effective_prompt),
    )?;

    let verification = if mutating {
        let check = execute_named_tool(service, "build.cargo_check", json!({}), "post-agent-check");
        Some(check)
    } else {
        None
    };

    let tx_status = if mutating {
        Some(execute_named_tool(
            service,
            "source.transaction_status",
            json!({}),
            "post-agent-tx-status",
        ))
    } else {
        None
    };

    let evidence_path = write_agent_evidence(
        service.engine.tools().session().directory.as_path(),
        action,
        prompt,
        &model,
        &result,
        tx_id.as_deref(),
        verification.as_ref(),
        tx_status.as_ref(),
    )?;

    let verification_ok = verification
        .as_ref()
        .map(tool_result_success)
        .unwrap_or(true);

    match output {
        OutputMode::Human => {
            println!("{}", result.text);
            eprintln!("Grounding : VERIFIED");
            eprintln!("Evidence  : {} structured tool call(s)", result.evidence.len());
            for evidence in &result.evidence {
                eprintln!(
                    "  [{}] {}{}",
                    if evidence.is_error { "FAIL" } else { "PASS" },
                    evidence.tool,
                    if evidence.mutating { " [mutating]" } else { "" }
                );
            }
            if mutating {
                eprintln!(
                    "Post-check : {}",
                    if verification_ok { "PASS" } else { "FAIL - transaction remains active" }
                );
            }
            eprintln!("Evidence file: {}", evidence_path.display());
            eprintln!("Iterations: {}", result.iterations);
        }
        OutputMode::Json => println!(
            "{}",
            serde_json::to_string_pretty(&json!({
                "schema_version":1,
                "mode":action,
                "grounding":"verified",
                "model":model,
                "text":result.text,
                "iterations":result.iterations,
                "evidence":result.evidence,
                "transaction_id":tx_id,
                "verification":verification,
                "transaction_status":tx_status,
                "evidence_file":evidence_path,
                "success":verification_ok
            }))
            .map_err(|e| e.to_string())?
        ),
        OutputMode::Jsonl => emit_event(output, "agent_finished", json!({
            "mode":action,
            "grounding":"verified",
            "model":model,
            "text":result.text,
            "iterations":result.iterations,
            "evidence":result.evidence,
            "transaction_id":tx_id,
            "verification":verification,
            "transaction_status":tx_status,
            "evidence_file":evidence_path,
            "success":verification_ok
        })),
    }

    if !verification_ok {
        return Err(format!(
            "{action} completed edits but post-agent cargo check failed; review or roll back the active transaction"
        ));
    }
    Ok(())
}

fn ensure_active_transaction(
    service: &mut CortexService,
    label: &str,
    reuse_transaction: bool,
) -> Result<String, String> {
    let status = execute_named_tool(
        service,
        "source.transaction_status",
        json!({}),
        "ensure-tx-status",
    );
    if status.is_error {
        return Err(status
            .output
            .get("error")
            .and_then(Value::as_str)
            .unwrap_or("could not read transaction status")
            .to_string());
    }
    if let Some(id) = status
        .output
        .pointer("/transaction/id")
        .and_then(Value::as_str)
    {
        if reuse_transaction {
            return Ok(id.to_string());
        }
        return Err(format!(
            "an active Cortex transaction already exists: {id}; commit/rollback it first or rerun with --reuse-transaction intentionally"
        ));
    }

    let begin = execute_named_tool(
        service,
        "source.begin_transaction",
        json!({"label": format!("{label}-{}", unix_ms())}),
        "ensure-tx-begin",
    );
    if begin.is_error {
        return Err(begin
            .output
            .get("error")
            .and_then(Value::as_str)
            .unwrap_or("could not begin transaction")
            .to_string());
    }
    begin
        .output
        .get("transaction_id")
        .and_then(Value::as_str)
        .map(str::to_string)
        .ok_or_else(|| "transaction begin returned no transaction id".to_string())
}

fn execute_named_tool(
    service: &mut CortexService,
    name: &str,
    arguments: Value,
    call_id: &str,
) -> open2d_cortex_protocol::ToolResultInput {
    service.engine.tools_mut().execute(&ToolCall {
        call_id: call_id.into(),
        name: name.into(),
        arguments,
    })
}

fn tool_result_success(result: &open2d_cortex_protocol::ToolResultInput) -> bool {
    !result.is_error
        && result
            .output
            .get("success")
            .and_then(Value::as_bool)
            .is_none_or(|success| success)
}

fn write_agent_evidence(
    session_dir: &Path,
    mode: &str,
    prompt: &str,
    model: &str,
    result: &AgentTurnResult,
    transaction_id: Option<&str>,
    verification: Option<&open2d_cortex_protocol::ToolResultInput>,
    transaction_status: Option<&open2d_cortex_protocol::ToolResultInput>,
) -> Result<PathBuf, String> {
    let artifacts = session_dir.join("artifacts");
    fs::create_dir_all(&artifacts).map_err(|e| e.to_string())?;
    let path = artifacts.join(format!("cortex-{mode}-evidence-{}.json", unix_ms()));
    let report = json!({
        "schema_version": 2,
        "mode": mode,
        "grounding": "verified",
        "prompt": prompt,
        "model": model,
        "iterations": result.iterations,
        "evidence": result.evidence,
        "tool_result_count": result.tool_results.len(),
        "response_id": result.last_response_id,
        "transaction_id": transaction_id,
        "verification": verification,
        "transaction_status": transaction_status
    });
    fs::write(
        &path,
        serde_json::to_vec_pretty(&report).map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())?;
    Ok(path)
}

fn build_command(service: &mut CortexService, args: &[String]) -> Result<(), String> {
    let command = args
        .iter()
        .find(|arg| !arg.starts_with("--"))
        .map(String::as_str)
        .unwrap_or("check");
    let output = output_mode(args);
    let tool_name = match command {
        "fmt" | "fmt-check" => "build.cargo_fmt_check",
        "check" => "build.cargo_check",
        "test-compile" | "test-no-run" => "build.cargo_test",
        "test" => "build.cargo_test_run",
        "clippy" | "lint" => "build.clippy",
        "certify" => "build.certify",
        other => return Err(format!(
            "unknown build command: {other}; use fmt-check, check, test-compile, test, clippy, or certify"
        )),
    };
    emit_event(output, "build_started", json!({"command":command,"tool":tool_name}));
    let result = execute_named_tool(service, tool_name, json!({}), "cli-build");
    let ok = tool_result_success(&result);
    match output {
        OutputMode::Human => println!(
            "{}",
            serde_json::to_string_pretty(&result.output).map_err(|e| e.to_string())?
        ),
        OutputMode::Json => println!(
            "{}",
            serde_json::to_string_pretty(&json!({
                "schema_version":1,
                "command":command,
                "success":ok,
                "result":result.output
            }))
            .map_err(|e| e.to_string())?
        ),
        OutputMode::Jsonl => emit_event(output, "build_finished", json!({
            "command":command,
            "success":ok,
            "result":result.output
        })),
    }
    if ok { Ok(()) } else { Err(format!("build command `{command}` failed")) }
}

fn session_command(project_root: &Path, args: &[String]) -> Result<(), String> {
    let root = project_root.join(".open2d").join("sessions");
    let command = args.first().map(String::as_str).unwrap_or("latest");
    match command {
        "list" => {
            for id in list_session_ids(&root)? {
                println!("{id}");
            }
        }
        "latest" => {
            let id = latest_session_id(&root)?
                .ok_or_else(|| "no Open2D development sessions found".to_string())?;
            println!("{}", root.join(&id).display());
        }
        "show" => {
            let id = resolve_session_id(&root, args.get(1).map(String::as_str))?;
            let path = root.join(id).join("session.json");
            let text = fs::read_to_string(&path)
                .map_err(|e| format!("could not read {}: {e}", path.display()))?;
            println!("{text}");
        }
        "artifacts" => {
            let id = resolve_session_id(&root, args.get(1).map(String::as_str))?;
            let artifacts = root.join(id).join("artifacts");
            if artifacts.is_dir() {
                let mut files = fs::read_dir(&artifacts)
                    .map_err(|e| e.to_string())?
                    .filter_map(Result::ok)
                    .filter(|entry| entry.path().is_file())
                    .map(|entry| entry.path())
                    .collect::<Vec<_>>();
                files.sort();
                for path in files {
                    println!("{}", path.display());
                }
            }
        }
        other => return Err(format!(
            "unknown session command: {other}; use list, latest, show [id|latest], or artifacts [id|latest]"
        )),
    }
    Ok(())
}

fn list_session_ids(root: &Path) -> Result<Vec<String>, String> {
    if !root.is_dir() {
        return Ok(Vec::new());
    }
    let mut ids = fs::read_dir(root)
        .map_err(|e| e.to_string())?
        .filter_map(Result::ok)
        .filter(|entry| entry.path().is_dir())
        .filter_map(|entry| entry.file_name().into_string().ok())
        .collect::<Vec<_>>();
    ids.sort();
    ids.reverse();
    Ok(ids)
}

fn latest_session_id(root: &Path) -> Result<Option<String>, String> {
    Ok(list_session_ids(root)?.into_iter().next())
}

fn resolve_session_id(root: &Path, value: Option<&str>) -> Result<String, String> {
    match value.unwrap_or("latest") {
        "latest" => latest_session_id(root)?
            .ok_or_else(|| "no Open2D development sessions found".to_string()),
        id if !id.contains('/') && !id.contains('\\') && id != "." && id != ".." => {
            let path = root.join(id);
            if path.is_dir() {
                Ok(id.to_string())
            } else {
                Err(format!("session not found: {id}"))
            }
        }
        _ => Err("invalid session id".into()),
    }
}

fn logs_command(project_root: &Path, args: &[String]) -> Result<(), String> {
    let root = project_root.join("logs").join("sessions");
    let command = args.first().map(String::as_str).unwrap_or("latest");
    match command {
        "list" => {
            if !root.is_dir() {
                return Ok(());
            }
            let mut files = fs::read_dir(&root)
                .map_err(|e| e.to_string())?
                .filter_map(Result::ok)
                .filter(|entry| entry.path().is_file())
                .map(|entry| entry.file_name().to_string_lossy().to_string())
                .collect::<Vec<_>>();
            files.sort();
            files.reverse();
            for file in files {
                println!("{file}");
            }
        }
        "latest" => {
            let lines = args.get(1).and_then(|v| v.parse::<usize>().ok()).unwrap_or(80);
            let path = root.join("LATEST_CORTEX_CHECKPOINT.log");
            print_tail(&path, lines)?;
        }
        "tail" => {
            let name = args.get(1).map(String::as_str).unwrap_or("LATEST_CORTEX_CHECKPOINT.log");
            if name.contains('/') || name.contains('\\') || name == "." || name == ".." {
                return Err("log name must be a file under logs/sessions".into());
            }
            let lines = args.get(2).and_then(|v| v.parse::<usize>().ok()).unwrap_or(80);
            print_tail(&root.join(name), lines)?;
        }
        other => return Err(format!(
            "unknown logs command: {other}; use list, latest [lines], or tail [file] [lines]"
        )),
    }
    Ok(())
}

fn print_tail(path: &Path, lines: usize) -> Result<(), String> {
    let text = fs::read_to_string(path)
        .map_err(|e| format!("could not read {}: {e}", path.display()))?;
    let all = text.lines().collect::<Vec<_>>();
    let start = all.len().saturating_sub(lines.clamp(1, 10_000));
    for line in &all[start..] {
        println!("{line}");
    }
    Ok(())
}

fn certify_command(
    project_root: &Path,
    service: &mut CortexService,
    args: &[String],
) -> Result<(), String> {
    let output = output_mode(args);
    let definitions = service.engine.tools().definitions();
    let tool_registry = certify_tool_definitions(&definitions);
    let tool_registry_ok = tool_registry
        .get("ok")
        .and_then(Value::as_bool)
        .unwrap_or(false);

    let model = service
        .engine
        .provider()
        .resolve_model()
        .map_err(|e| e.to_string())?;
    let provider_smoke = run_provider_tool_smoke(service.engine.provider(), &model, &definitions);
    let provider_smoke_ok = provider_smoke.is_ok();

    let transaction_smoke = transaction_smoke_test(project_root, service);
    let transaction_smoke_ok = transaction_smoke.is_ok();

    emit_event(output, "certification_stage", json!({"stage":"build","status":"running"}));
    let build = execute_named_tool(service, "build.certify", json!({}), "coding-cert-build");
    let build_ok = tool_result_success(&build);

    let success = tool_registry_ok && provider_smoke_ok && transaction_smoke_ok && build_ok;
    let report = json!({
        "schema_version":1,
        "certification":"open2d_cortex_coding",
        "success":success,
        "model":model,
        "tool_registry":tool_registry,
        "structured_tool_call":match provider_smoke { Ok(value) => value, Err(error) => json!({"error":error}) },
        "transaction_smoke":match transaction_smoke { Ok(value) => value, Err(error) => json!({"error":error}) },
        "build":build.output
    });
    match output {
        OutputMode::Human => {
            println!("OPEN2D CORTEX CODING CERTIFICATION");
            println!("Tool registry      : {}", if tool_registry_ok { "PASS" } else { "FAIL" });
            println!("Structured tool use: {}", if provider_smoke_ok { "PASS" } else { "FAIL" });
            println!("Transaction safety : {}", if transaction_smoke_ok { "PASS" } else { "FAIL" });
            println!("Build gate         : {}", if build_ok { "PASS" } else { "FAIL" });
            println!("Overall            : {}", if success { "READY" } else { "FAILED" });
        }
        OutputMode::Json => println!("{}", serde_json::to_string_pretty(&report).map_err(|e| e.to_string())?),
        OutputMode::Jsonl => emit_event(output, "certification_finished", report),
    }
    if success { Ok(()) } else { Err("Open2D Cortex coding certification failed".into()) }
}

fn transaction_smoke_test(
    project_root: &Path,
    service: &mut CortexService,
) -> Result<Value, String> {
    let status = execute_named_tool(
        service,
        "source.transaction_status",
        json!({}),
        "cert-tx-status",
    );
    if status
        .output
        .get("transaction")
        .is_some_and(|value| !value.is_null())
    {
        return Err("an active source transaction already exists; finish or roll it back before coding certification".into());
    }
    let relative = ".open2d/cortex/certification/transaction-smoke.txt";
    let path = project_root.join(relative);
    if path.exists() {
        fs::remove_file(&path).map_err(|e| e.to_string())?;
    }
    let begin = execute_named_tool(
        service,
        "source.begin_transaction",
        json!({"label":"certification-smoke"}),
        "cert-tx-begin",
    );
    if begin.is_error {
        return Err("could not begin certification transaction".into());
    }
    let write = execute_named_tool(
        service,
        "source.write_text",
        json!({"path":relative,"content":"open2d cortex transaction certification\n"}),
        "cert-tx-write",
    );
    if write.is_error {
        let _ = execute_named_tool(service, "source.rollback", json!({}), "cert-tx-rollback-write-error");
        return Err("could not write certification transaction file".into());
    }
    let rollback = execute_named_tool(
        service,
        "source.rollback",
        json!({}),
        "cert-tx-rollback",
    );
    if rollback.is_error || path.exists() {
        return Err("transaction rollback certification failed".into());
    }
    Ok(json!({"success":true,"path":relative,"rolled_back":true}))
}

fn print_cli_help() {
    println!("Open2D Cortex CLI");
    println!();
    println!("Core:");
    println!("  status");
    println!("  doctor [full] [--json]");
    println!("  chat <prompt> [--json|--jsonl]");
    println!("  inspect <prompt> [--json|--jsonl]");
    println!("  plan <request> [--json|--jsonl]");
    println!("  apply <request> [--reuse-transaction] [--json|--jsonl]");
    println!("  repair <request> [--reuse-transaction] [--json|--jsonl]");
    println!("  certify [--json|--jsonl]");
    println!("  serve [port]");
    println!();
    println!("Models:");
    println!("  models");
    println!("  model current [role]");
    println!("  model roles");
    println!("  model set [role] <model-id>");
    println!("  model clear [role]");
    println!("  roles: default, chat, tool, vision, embedding");
    println!();
    println!("Tools:");
    println!("  tools list [--json]");
    println!("  tools describe <name> [--json]");
    println!("  tools certify [--json]");
    println!("  tools test <name> [json-args] [--allow-mutation]");
    println!("  tools test-all");
    println!("  tool <name> [json-args]        (low-level compatibility)");
    println!();
    println!("Build:");
    println!("  build fmt-check|check|test-compile|test|clippy|certify [--json|--jsonl]");
    println!();
    println!("Sessions / logs:");
    println!("  session list|latest|show [id|latest]|artifacts [id|latest]");
    println!("  logs list|latest [lines]|tail [file] [lines]");
    println!();
    println!("Transactions:");
    println!("  tx status");
    println!("  tx files");
    println!("  tx begin [label]");
    println!("  tx checkpoint <path>");
    println!("  tx commit [--force]    (cargo check required unless forced)");
    println!("  tx rollback");
}

fn unix_ms() -> u128 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis()
}

fn configured_lm_timeout() -> Duration {
    let seconds = env::var("OPEN2D_LMSTUDIO_TIMEOUT_SECONDS")
        .ok()
        .and_then(|value| value.parse::<u64>().ok())
        .unwrap_or(120)
        .clamp(30, 900);
    Duration::from_secs(seconds)
}

fn configured_agent_deadline() -> Duration {
    let seconds = env::var("OPEN2D_CORTEX_TOTAL_TIMEOUT_SECONDS")
        .ok()
        .and_then(|value| value.parse::<u64>().ok())
        .unwrap_or(300)
        .clamp(60, 1800);
    Duration::from_secs(seconds)
}

fn configured_agent_iterations() -> usize {
    env::var("OPEN2D_CORTEX_MAX_ITERATIONS")
        .ok()
        .and_then(|value| value.parse::<usize>().ok())
        .unwrap_or(8)
        .clamp(1, 24)
}

fn print_request_header(
    request_kind: &str,
    model: &str,
    mode: AgentMode,
    provider_timeout: Duration,
    total_deadline_seconds: Option<u64>,
    grounding: &str,
) {
    eprintln!();
    eprintln!("OPEN2D CORTEX {request_kind}");
    eprintln!("Provider  : LM Studio");
    eprintln!("Model     : {model}");
    eprintln!("Mode      : {}", mode_name(mode));
    eprintln!("HTTP limit: {} seconds per provider response", provider_timeout.as_secs());
    if let Some(seconds) = total_deadline_seconds {
        eprintln!("Loop limit: {seconds} seconds total project-agent budget");
    }
    eprintln!("Grounding : {grounding}");
    eprintln!("Cancel    : Ctrl+C");
    eprintln!();
}

fn run_with_progress<T, F>(
    label: &'static str,
    advertised_limit: Duration,
    output: OutputMode,
    work: F,
) -> Result<T, String>
where
    F: FnOnce() -> Result<T, String>,
{
    let done = Arc::new(AtomicBool::new(false));
    let ticker_done = Arc::clone(&done);
    let ticker = thread::spawn(move || {
        let started = Instant::now();
        let mut last_reported = 0u64;
        while !ticker_done.load(Ordering::Relaxed) {
            thread::sleep(Duration::from_secs(1));
            let elapsed = started.elapsed().as_secs();
            if elapsed >= last_reported + 10 && !ticker_done.load(Ordering::Relaxed) {
                last_reported = elapsed;
                match output {
                    OutputMode::Human => eprintln!(
                        "Cortex {label} active... elapsed {elapsed}s / advertised limit {}s",
                        advertised_limit.as_secs()
                    ),
                    OutputMode::Json => {},
                    OutputMode::Jsonl => emit_event(output, "progress", json!({
                        "label":label,
                        "elapsed_seconds":elapsed,
                        "advertised_limit_seconds":advertised_limit.as_secs()
                    })),
                }
            }
        }
    });

    let result = work();
    done.store(true, Ordering::Relaxed);
    let _ = ticker.join();
    result
}

struct CortexService {
    engine: CortexEngine,
    rpc_token: String,
}

impl RpcHandler for CortexService {
    fn handle(&mut self, request: RpcRequest) -> RpcResponse {
        let id = request.id.clone();
        if request.auth_token.as_deref() != Some(self.rpc_token.as_str()) {
            return RpcResponse::error(id, "Cortex RPC authentication failed");
        }
        match request.method.as_str() {
            "health" => RpcResponse::ok(
                id,
                json!({"service":"open2d_cortex","status":"ready"}),
            ),
            "tools.list" => RpcResponse::ok(
                id,
                json!({"tools": self.engine.tools().definitions()}),
            ),
            "tools.call" => {
                let name = request
                    .params
                    .get("name")
                    .and_then(Value::as_str)
                    .unwrap_or_default();
                let arguments = request
                    .params
                    .get("arguments")
                    .cloned()
                    .unwrap_or_else(|| json!({}));
                let result = self.engine.tools_mut().execute(&ToolCall {
                    call_id: request.id.clone(),
                    name: name.into(),
                    arguments,
                });
                if result.is_error {
                    RpcResponse::error(
                        id,
                        result
                            .output
                            .get("error")
                            .and_then(Value::as_str)
                            .unwrap_or("tool failed"),
                    )
                } else {
                    RpcResponse::ok(id, result.output)
                }
            }
            "models.list" => match self.engine.provider().list_models() {
                Ok(models) => RpcResponse::ok(id, json!({"models": models})),
                Err(error) => RpcResponse::error(id, error.to_string()),
            },
            "agent.ask" | "agent.chat" => {
                let Some(prompt) = request.params.get("prompt").and_then(Value::as_str) else {
                    return RpcResponse::error(id, "agent.chat requires prompt");
                };
                match self.engine.chat(prompt) {
                    Ok(result) => RpcResponse::ok(
                        id,
                        serde_json::to_value(result).unwrap_or(Value::Null),
                    ),
                    Err(error) => RpcResponse::error(id, error),
                }
            }
            "agent.inspect" | "agent.plan" => {
                let Some(prompt) = request.params.get("prompt").and_then(Value::as_str) else {
                    return RpcResponse::error(id, "read-only project agent requires prompt");
                };
                self.engine.set_mode(AgentMode::Observe);
                match self.engine.run(prompt) {
                    Ok(result) => RpcResponse::ok(
                        id,
                        serde_json::to_value(result).unwrap_or(Value::Null),
                    ),
                    Err(error) => RpcResponse::error(id, error),
                }
            }
            "agent.apply" | "agent.repair" => {
                let Some(prompt) = request.params.get("prompt").and_then(Value::as_str) else {
                    return RpcResponse::error(id, "mutating project agent requires prompt");
                };
                self.engine.set_mode(AgentMode::WorkspaceAutonomy);
                match self.engine.run(prompt) {
                    Ok(result) => RpcResponse::ok(
                        id,
                        serde_json::to_value(result).unwrap_or(Value::Null),
                    ),
                    Err(error) => RpcResponse::error(id, error),
                }
            }
            "session.info" => RpcResponse::ok(
                id,
                json!({
                    "id": self.engine.tools().session().id,
                    "directory": self.engine.tools().session().directory
                }),
            ),
            _ => RpcResponse::error(id, format!("unknown RPC method: {}", request.method)),
        }
    }
}

fn agent_mode_from_env() -> AgentMode {
    match env::var("OPEN2D_CORTEX_MODE")
        .unwrap_or_else(|_| "workspace_autonomy".into())
        .to_ascii_lowercase()
        .as_str()
    {
        "observe" => AgentMode::Observe,
        "guided" => AgentMode::Guided,
        _ => AgentMode::WorkspaceAutonomy,
    }
}

fn mode_name(mode: AgentMode) -> &'static str {
    match mode {
        AgentMode::Observe => "Observe",
        AgentMode::Guided => "Guided",
        AgentMode::WorkspaceAutonomy => "Workspace Autonomy",
    }
}

fn find_project_root(mut path: PathBuf) -> Result<PathBuf, String> {
    loop {
        if path.join("Cargo.toml").is_file() {
            return Ok(path);
        }
        if !path.pop() {
            return Err("could not find Open2D Cargo.toml from current directory".into());
        }
    }
}

fn ensure_rpc_token(project_root: &Path) -> Result<String, String> {
    let dir = project_root.join(".open2d").join("cortex");
    fs::create_dir_all(&dir).map_err(|e| e.to_string())?;
    let path = dir.join("rpc.token");
    if let Ok(existing) = fs::read_to_string(&path) {
        let token = existing.trim();
        if token.len() >= 24 {
            return Ok(token.to_string());
        }
    }
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_nanos();
    let token = format!(
        "{:x}{:x}{:x}",
        now,
        std::process::id(),
        now.rotate_left(37)
    );
    fs::write(&path, token.as_bytes()).map_err(|e| e.to_string())?;
    Ok(token)
}
