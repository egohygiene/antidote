//! Framework-independent Antidote domain and application boundary.
//!
//! Issue #11 will introduce the authoritative session state machine. This
//! crate intentionally contains no Tauri, storage, Python, audio-model, or
//! publication dependencies.

pub use antidote_contracts as contracts;

/// Honest implementation status exposed to scaffold smoke tests.
pub const IMPLEMENTATION_STATUS: &str = "contract-foundation-only";

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn status_does_not_claim_domain_implementation() {
        assert_eq!(IMPLEMENTATION_STATUS, "contract-foundation-only");
    }
}
