//! Local append-only persistence adapters for Antidote.
//!
//! `SQLite` stores immutable event envelopes and disposable projections. Large
//! or sensitive payloads remain in a content-addressed filesystem. Adapter
//! errors are deliberately redacted when they cross into `antidote-core`.

mod artifact;
mod error;
mod sqlite;

pub use artifact::{ContentAddressedStore, StoredObject};
pub use error::{StoreError, StoreResult};
pub use sqlite::{
    PayloadClassification, PayloadReference, ProjectionKind, ProjectionRecord, SqliteEventStore,
};

/// Honest implementation status exposed to workspace smoke tests.
pub const IMPLEMENTATION_STATUS: &str = "append-only-sqlite-and-content-store-v1";

#[cfg(test)]
mod tests {
    use super::IMPLEMENTATION_STATUS;

    #[test]
    fn status_names_the_implemented_storage_boundary() {
        assert_eq!(
            IMPLEMENTATION_STATUS,
            "append-only-sqlite-and-content-store-v1"
        );
    }
}
