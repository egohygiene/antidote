//! Generated contract projections and runtime validation against canonical schemas.

mod generated;

use serde_json::Value;

pub use generated::*;

/// One canonical JSON Schema embedded from the repository-owned source.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ContractSchema {
    pub name: &'static str,
    pub filename: &'static str,
    pub id: &'static str,
    pub document: &'static str,
}

/// Validate a JSON value against a named canonical contract.
///
/// # Errors
///
/// Returns a descriptive error when the schema name is unknown, the checked-in
/// schema cannot be parsed or compiled, or the value violates the schema.
pub fn validate_contract(name: &str, value: &Value) -> Result<(), String> {
    let contract = CONTRACT_SCHEMAS
        .iter()
        .find(|candidate| candidate.name == name)
        .ok_or_else(|| format!("unknown Antidote contract: {name}"))?;
    let schema: Value = serde_json::from_str(contract.document)
        .map_err(|error| format!("invalid schema {}: {error}", contract.filename))?;
    let validator = jsonschema::draft202012::options()
        .should_validate_formats(true)
        .build(&schema)
        .map_err(|error| format!("cannot compile schema {}: {error}", contract.filename))?;
    let failures = validator
        .iter_errors(value)
        .map(|error| format!("{}: {error}", error.instance_path()))
        .collect::<Vec<_>>();
    if failures.is_empty() {
        Ok(())
    } else {
        Err(failures.join("\n"))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde::Deserialize;

    #[derive(Debug, Deserialize)]
    struct FixtureSuite {
        cases: Vec<FixtureCase>,
    }

    #[derive(Debug, Deserialize)]
    struct FixtureCase {
        name: String,
        contract: String,
        valid: bool,
        data: Value,
    }

    #[test]
    fn canonical_fixtures_have_the_expected_validity() {
        let fixtures: FixtureSuite =
            serde_json::from_str(include_str!("../../../contracts/fixtures/cases.json"))
                .expect("fixture suite must be valid JSON");

        for fixture in fixtures.cases {
            let result = validate_contract(&fixture.contract, &fixture.data);
            assert_eq!(
                result.is_ok(),
                fixture.valid,
                "fixture {} produced {result:?}",
                fixture.name
            );
        }
    }

    #[test]
    fn schema_names_and_ids_are_unique() {
        let mut names = CONTRACT_SCHEMAS
            .iter()
            .map(|schema| schema.name)
            .collect::<Vec<_>>();
        names.sort_unstable();
        names.dedup();
        assert_eq!(names.len(), CONTRACT_SCHEMAS.len());

        let mut ids = CONTRACT_SCHEMAS
            .iter()
            .map(|schema| schema.id)
            .collect::<Vec<_>>();
        ids.sort_unstable();
        ids.dedup();
        assert_eq!(ids.len(), CONTRACT_SCHEMAS.len());
    }
}
