use haven_core::ProgressionCatalog;
use std::sync::OnceLock;

const EMBEDDED_PROGRESSION_CATALOG: &str =
    include_str!("../../../content/progression/havenwild_progression_catalog_v0_1.json");

static CATALOG: OnceLock<Result<ProgressionCatalog, String>> = OnceLock::new();

pub(crate) fn progression_catalog() -> Result<&'static ProgressionCatalog, String> {
    CATALOG
        .get_or_init(|| {
            let catalog: ProgressionCatalog = serde_json::from_str(EMBEDDED_PROGRESSION_CATALOG)
                .map_err(|error| format!("failed to parse progression catalog: {error}"))?;
            catalog.validate()?;
            Ok(catalog)
        })
        .as_ref()
        .map_err(Clone::clone)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn embedded_progression_catalog_is_valid() {
        let catalog = progression_catalog().expect("progression catalog should validate");
        assert_eq!(catalog.classes.len(), 10);
        assert!(catalog.professions.len() >= 20);
        assert!(catalog.general_skills.len() >= 8);
    }
}
