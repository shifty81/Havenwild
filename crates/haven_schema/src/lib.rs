//! Havenwild schema diagnostics boundary.
//!
//! Saves/content remain Havenwild-owned. This layer supplies stable error paths
//! today and is the integration seam for schemars/serde_path_to_error after the
//! first dependency-certification gate.

use serde::{Deserialize, Serialize};
use serde_json::Value;

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SchemaIssue {
    pub path: String,
    pub message: String,
}

pub fn validate_schema_tag(document: &Value, expected: &str) -> Vec<SchemaIssue> {
    match document.get("schema").and_then(Value::as_str) {
        Some(actual) if actual == expected => Vec::new(),
        Some(actual) => vec![SchemaIssue {
            path: "$.schema".to_string(),
            message: format!("expected {expected}, found {actual}"),
        }],
        None => vec![SchemaIssue {
            path: "$.schema".to_string(),
            message: format!("missing required schema tag {expected}"),
        }],
    }
}

pub fn validate_required_fields(document: &Value, fields: &[&str]) -> Vec<SchemaIssue> {
    fields
        .iter()
        .filter(|field| document.get(**field).is_none())
        .map(|field| SchemaIssue {
            path: format!("$.{field}"),
            message: "required field is missing".to_string(),
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn schema_tag_reports_exact_path() {
        let value = serde_json::json!({"schema":"wrong"});
        let issues = validate_schema_tag(&value, "havenwild.test.v1");
        assert_eq!(issues[0].path, "$.schema");
    }
}
