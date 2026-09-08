//! Cortex agent orchestration independent of Foundry, VS Code and model host.

use open2d_cortex_protocol::{
    ModelRequest, ModelResponse, TextProvider, ToolCall, ToolExecutor, ToolResultInput,
};
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::time::{Duration, Instant};

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum AgentMode {
    Observe,
    Guided,
    WorkspaceAutonomy,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct AgentSettings {
    pub mode: AgentMode,
    pub max_tool_iterations: usize,
    pub max_elapsed_seconds: u64,
    pub max_tool_result_bytes: usize,
    pub system_instructions: String,
}

impl Default for AgentSettings {
    fn default() -> Self {
        Self {
            mode: AgentMode::Guided,
            max_tool_iterations: 8,
            max_elapsed_seconds: 300,
            max_tool_result_bytes: 32 * 1024,
            system_instructions: default_system_instructions(),
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct AgentToolEvidence {
    pub tool: String,
    pub call_id: String,
    pub mutating: bool,
    pub is_error: bool,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct AgentTurnResult {
    pub text: String,
    pub iterations: usize,
    pub tool_results: Vec<ToolResultInput>,
    pub evidence: Vec<AgentToolEvidence>,
    pub last_response_id: Option<String>,
}

pub struct AgentEngine<P, T> {
    provider: P,
    tools: T,
    settings: AgentSettings,
}

impl<P, T> AgentEngine<P, T>
where
    P: TextProvider,
    T: ToolExecutor,
{
    pub fn new(provider: P, tools: T, settings: AgentSettings) -> Self {
        Self { provider, tools, settings }
    }

    pub fn provider(&self) -> &P { &self.provider }
    pub fn tools(&self) -> &T { &self.tools }
    pub fn tools_mut(&mut self) -> &mut T { &mut self.tools }

    pub fn set_mode(&mut self, mode: AgentMode) {
        self.settings.mode = mode;
    }

    pub fn settings(&self) -> &AgentSettings {
        &self.settings
    }

    pub fn chat(&self, prompt: &str) -> Result<AgentTurnResult, String> {
        let mut request = ModelRequest::user(prompt);
        request.instructions = Some(default_chat_instructions());

        let response = self.provider.respond(&request).map_err(|e| e.to_string())?;
        if !response.tool_calls.is_empty() {
            return Err(
                "Cortex chat received an unexpected tool call even though no tools were offered"
                    .into(),
            );
        }

        Ok(AgentTurnResult {
            text: response.output_text,
            iterations: 1,
            tool_results: Vec::new(),
            evidence: Vec::new(),
            last_response_id: response.id,
        })
    }

    pub fn run(&mut self, prompt: &str) -> Result<AgentTurnResult, String> {
        let definitions = self.tools.definitions();
        let mut request = ModelRequest::user(prompt);
        request.instructions = Some(self.settings.system_instructions.clone());
        request.tools = definitions.clone();

        let mut collected_results = Vec::new();
        let mut collected_evidence = Vec::new();
        let mut last_response: Option<ModelResponse> = None;
        let started = Instant::now();
        let max_elapsed = Duration::from_secs(self.settings.max_elapsed_seconds);

        for iteration in 1..=self.settings.max_tool_iterations {
            if started.elapsed() >= max_elapsed {
                return Err(format!(
                    "Cortex project-agent deadline exceeded after {} seconds before iteration {}",
                    self.settings.max_elapsed_seconds,
                    iteration
                ));
            }

            let response = self.provider.respond(&request).map_err(|e| e.to_string())?;

            if started.elapsed() >= max_elapsed {
                return Err(format!(
                    "Cortex project-agent deadline exceeded after {} seconds during iteration {}",
                    self.settings.max_elapsed_seconds,
                    iteration
                ));
            }
            let response_id = response.id.clone();
            if response.tool_calls.is_empty() {
                if iteration == 1 && !definitions.is_empty() {
                    let preview = response
                        .output_text
                        .chars()
                        .take(320)
                        .collect::<String>();
                    return Err(format!(
                        "Cortex rejected an ungrounded model response: the provider/model did not emit a structured tool call on the required first turn. No claimed project inspection was accepted. Select a tool-capable LM Studio model or inspect its tool-call template. Model text preview: {preview}"
                    ));
                }

                return Ok(AgentTurnResult {
                    text: response.output_text,
                    iterations: iteration,
                    tool_results: collected_results,
                    evidence: collected_evidence,
                    last_response_id: response_id,
                });
            }

            let mut results = Vec::new();
            for call in &response.tool_calls {
                let definition = definitions.iter().find(|tool| tool.name == call.name);
                let mutating = definition.map(|tool| tool.mutating).unwrap_or(true);
                let result = if self.may_execute(call, &definitions) {
                    self.tools.execute(call)
                } else {
                    denied(call, self.settings.mode)
                };
                let result = bound_tool_result(result, self.settings.max_tool_result_bytes);
                collected_evidence.push(AgentToolEvidence {
                    tool: call.name.clone(),
                    call_id: call.call_id.clone(),
                    mutating,
                    is_error: result.is_error,
                });
                collected_results.push(result.clone());
                results.push(result);
            }

            request = ModelRequest {
                model: request.model.clone(),
                instructions: Some(self.settings.system_instructions.clone()),
                messages: Vec::new(),
                tools: definitions.clone(),
                previous_response_id: response_id,
                tool_results: results,
                images: Vec::new(),
            };
            last_response = Some(response);
        }

        Err(format!(
            "Cortex exceeded {} tool iterations; last response id: {:?}",
            self.settings.max_tool_iterations,
            last_response.and_then(|response| response.id)
        ))
    }

    fn may_execute(&self, call: &ToolCall, definitions: &[open2d_cortex_protocol::ToolDefinition]) -> bool {
        let mutating = definitions.iter().find(|tool| tool.name == call.name).map(|tool| tool.mutating).unwrap_or(true);
        match self.settings.mode {
            AgentMode::Observe => !mutating,
            AgentMode::Guided => !mutating,
            AgentMode::WorkspaceAutonomy => true,
        }
    }
}


fn bound_tool_result(mut result: ToolResultInput, max_bytes: usize) -> ToolResultInput {
    let max_bytes = max_bytes.max(4096);
    let Ok(encoded) = serde_json::to_string(&result.output) else {
        return result;
    };
    if encoded.len() <= max_bytes {
        return result;
    }

    let preview_budget = max_bytes.saturating_sub(768).max(1024);
    let preview = encoded.chars().take(preview_budget).collect::<String>();
    result.output = json!({
        "truncated": true,
        "original_bytes": encoded.len(),
        "preview": preview,
        "hint": "Cortex bounded this tool result to protect the model context window. Use a narrower source.read/source.search/source.list request if more detail is required."
    });
    result
}

fn denied(call: &ToolCall, mode: AgentMode) -> ToolResultInput {
    ToolResultInput {
        call_id: call.call_id.clone(),
        is_error: true,
        output: json!({
            "error": "tool requires mutation permission",
            "tool": call.name,
            "agent_mode": mode,
            "hint": "switch this Cortex session to workspace_autonomy or explicitly approve the transaction"
        }),
    }
}

pub fn default_chat_instructions() -> String {
    r#"You are Open2D Cortex in general chat mode.

This mode has no project tools and is intentionally ungrounded.
Answer general questions, brainstorming prompts, and simple conversational checks concisely.
Do not claim that you inspected files, ran commands, queried the current project, or verified runtime state.
If the user asks for current Open2D project facts, tell them to use Cortex inspect mode."#
        .into()
}

pub fn default_system_instructions() -> String {
    r#"You are Open2D Cortex, the project-aware development agent for Open2D Foundry.

Work from current source truth. Prefer source/project/runtime evidence over old planning notes.
Use the provided structured tools rather than inventing file contents or shell results. On the first turn of every project-aware request, obtain structured project evidence before making project-specific claims.
Before source mutation, begin a Cortex transaction. Keep edits bounded to the active Open2D workspace.
After Rust edits, verify with structured Cargo checks. Read diagnostics and repair compile failures.
When runtime or UI behavior matters, launch the owned development process, capture evidence, and inspect it.
Generated images are draft Cortex artifacts until explicitly promoted into project content.
Do not access paths outside the active workspace, install software, change global settings, or control unowned processes.
Summarize concrete files changed, verification performed, runtime/visual evidence, and any remaining uncertainty."#.into()
}


#[cfg(test)]
mod tests {
    use super::*;
    use open2d_cortex_protocol::{
        ProviderError, ToolDefinition, ToolExecutor, ToolResultInput,
    };
    use serde_json::json;

    struct PlainTextProvider;

    impl TextProvider for PlainTextProvider {
        fn provider_id(&self) -> &str {
            "plain"
        }

        fn list_models(&self) -> Result<Vec<String>, ProviderError> {
            Ok(vec!["plain".into()])
        }

        fn respond(&self, _request: &ModelRequest) -> Result<ModelResponse, ProviderError> {
            Ok(ModelResponse {
                id: Some("resp-1".into()),
                output_text: "I inspected /invented/project with grep.".into(),
                tool_calls: Vec::new(),
                raw: json!({}),
            })
        }
    }

    struct ReadTool;

    impl ToolExecutor for ReadTool {
        fn definitions(&self) -> Vec<ToolDefinition> {
            vec![ToolDefinition {
                name: "project.status".into(),
                description: "Read project status".into(),
                parameters: json!({"type":"object","properties":{}}),
                mutating: false,
            }]
        }

        fn execute(&mut self, call: &ToolCall) -> ToolResultInput {
            ToolResultInput {
                call_id: call.call_id.clone(),
                output: json!({"ok":true}),
                is_error: false,
            }
        }
    }

    #[test]
    fn first_project_response_without_tool_call_is_rejected() {
        let mut engine = AgentEngine::new(
            PlainTextProvider,
            ReadTool,
            AgentSettings::default(),
        );
        let error = engine.run("Inspect this project").unwrap_err();
        assert!(error.contains("ungrounded model response"));
    }
    #[test]
    fn chat_does_not_offer_project_tools() {
        struct ChatProvider;

        impl TextProvider for ChatProvider {
            fn provider_id(&self) -> &str {
                "chat"
            }

            fn list_models(&self) -> Result<Vec<String>, ProviderError> {
                Ok(vec!["chat".into()])
            }

            fn respond(&self, request: &ModelRequest) -> Result<ModelResponse, ProviderError> {
                assert!(request.tools.is_empty());
                Ok(ModelResponse {
                    id: Some("chat-1".into()),
                    output_text: "ok".into(),
                    tool_calls: Vec::new(),
                    raw: json!({}),
                })
            }
        }

        let engine = AgentEngine::new(ChatProvider, ReadTool, AgentSettings::default());
        let result = engine.chat("test").unwrap();
        assert_eq!(result.text, "ok");
        assert_eq!(result.iterations, 1);
    }


    #[test]
    fn oversized_tool_results_are_bounded() {
        let large = "x".repeat(200_000);
        let result = ToolResultInput {
            call_id: "large".into(),
            output: json!({"text": large}),
            is_error: false,
        };
        let bounded = bound_tool_result(result, 32 * 1024);
        assert_eq!(
            bounded.output.get("truncated").and_then(|value| value.as_bool()),
            Some(true)
        );
        assert!(
            serde_json::to_string(&bounded.output).unwrap().len() < 40 * 1024
        );
    }

}
