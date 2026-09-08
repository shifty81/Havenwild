//! Deterministic Havenwild behavior-graph authoring contracts.
//!
//! The editor graph is authoring data. Compilation emits explicit deterministic
//! instructions; the graph is not a second arbitrary scripting runtime.

use haven_identity::HavenId;
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};
use std::path::Path;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum LogicNodeKind {
    EventInteract,
    EventEnter,
    ConditionFlag,
    ConditionHasItem,
    ActionSetFlag,
    ActionGiveItem,
    ActionPlaySound,
    ActionPlayAnimation,
    Branch,
    Sequence,
}

impl LogicNodeKind {
    pub fn label(self) -> &'static str {
        match self {
            Self::EventInteract => "On Interact",
            Self::EventEnter => "On Enter",
            Self::ConditionFlag => "Flag Condition",
            Self::ConditionHasItem => "Has Item",
            Self::ActionSetFlag => "Set Flag",
            Self::ActionGiveItem => "Give Item",
            Self::ActionPlaySound => "Play Sound",
            Self::ActionPlayAnimation => "Play Animation",
            Self::Branch => "Branch",
            Self::Sequence => "Sequence",
        }
    }
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct LogicNode {
    pub id: HavenId,
    pub kind: LogicNodeKind,
    pub label: String,
    pub position: [f32; 2],
    #[serde(default)]
    pub properties: BTreeMap<String, String>,
}

impl LogicNode {
    pub fn new(kind: LogicNodeKind, position: [f32; 2]) -> Self {
        Self {
            id: HavenId::new("logic_node"),
            label: kind.label().to_string(),
            kind,
            position,
            properties: BTreeMap::new(),
        }
    }
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct LogicLink {
    pub from_node: HavenId,
    pub to_node: HavenId,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct LogicGraph {
    pub schema: String,
    pub id: HavenId,
    pub display_name: String,
    pub nodes: Vec<LogicNode>,
    pub links: Vec<LogicLink>,
}

impl Default for LogicGraph {
    fn default() -> Self {
        let event = LogicNode::new(LogicNodeKind::EventInteract, [90.0, 120.0]);
        let action = LogicNode::new(LogicNodeKind::ActionPlaySound, [360.0, 120.0]);
        let links = vec![LogicLink { from_node: event.id.clone(), to_node: action.id.clone() }];
        Self {
            schema: "havenwild.logic_graph.v1".to_string(),
            id: HavenId::new("logic_graph"),
            display_name: "New Behavior".to_string(),
            nodes: vec![event, action],
            links,
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CompiledLogicInstruction {
    pub node_id: String,
    pub opcode: String,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CompiledLogicGraph {
    pub source_graph_id: String,
    pub instructions: Vec<CompiledLogicInstruction>,
}

impl LogicGraph {
    pub fn save_to_path(&self, path: &Path) -> Result<(), String> {
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent).map_err(|error| error.to_string())?;
        }
        let text = serde_json::to_string_pretty(self).map_err(|error| error.to_string())?;
        std::fs::write(path, format!("{text}\n")).map_err(|error| error.to_string())
    }

    pub fn validate(&self) -> Vec<String> {
        let ids: BTreeSet<&str> = self.nodes.iter().map(|node| node.id.as_str()).collect();
        let mut issues = Vec::new();
        for link in &self.links {
            if !ids.contains(link.from_node.as_str()) {
                issues.push(format!("Missing link source {}", link.from_node));
            }
            if !ids.contains(link.to_node.as_str()) {
                issues.push(format!("Missing link target {}", link.to_node));
            }
        }
        if !self.nodes.iter().any(|node| matches!(node.kind, LogicNodeKind::EventInteract | LogicNodeKind::EventEnter)) {
            issues.push("Behavior graph has no event entry node".to_string());
        }
        issues
    }

    pub fn compile(&self) -> Result<CompiledLogicGraph, Vec<String>> {
        let issues = self.validate();
        if !issues.is_empty() {
            return Err(issues);
        }
        let instructions = self
            .nodes
            .iter()
            .map(|node| CompiledLogicInstruction {
                node_id: node.id.to_string(),
                opcode: opcode(node.kind).to_string(),
            })
            .collect();
        Ok(CompiledLogicGraph {
            source_graph_id: self.id.to_string(),
            instructions,
        })
    }
}

fn opcode(kind: LogicNodeKind) -> &'static str {
    match kind {
        LogicNodeKind::EventInteract => "event.interact",
        LogicNodeKind::EventEnter => "event.enter",
        LogicNodeKind::ConditionFlag => "condition.flag",
        LogicNodeKind::ConditionHasItem => "condition.has_item",
        LogicNodeKind::ActionSetFlag => "action.set_flag",
        LogicNodeKind::ActionGiveItem => "action.give_item",
        LogicNodeKind::ActionPlaySound => "action.play_sound",
        LogicNodeKind::ActionPlayAnimation => "action.play_animation",
        LogicNodeKind::Branch => "logic.branch",
        LogicNodeKind::Sequence => "logic.sequence",
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn starter_graph_compiles_deterministically() {
        let graph = LogicGraph::default();
        let compiled = graph.compile().expect("starter graph should compile");
        assert_eq!(compiled.instructions.len(), 2);
        assert_eq!(compiled.instructions[0].opcode, "event.interact");
    }
}
