use std::error::Error;
use std::fmt::{Display, Formatter};
use std::path::PathBuf;

/// Detailed local storage failure that must not cross an untrusted interface.
#[derive(Debug)]
#[non_exhaustive]
pub enum StoreError {
    /// `SQLite` rejected an operation or a migration.
    Database(rusqlite::Error),
    /// A filesystem operation failed.
    Io(std::io::Error),
    /// An event or projection could not be encoded or decoded.
    Serialization(serde_json::Error),
    /// The event stream is not contiguous, immutable, or internally consistent.
    CorruptEventStream { session_id: String },
    /// An optimistic append observed a different current version.
    ConcurrencyConflict {
        session_id: String,
        expected: u64,
        actual: u64,
    },
    /// An identifier or content digest has an invalid shape.
    InvalidIdentifier,
    /// Content did not match the caller's expected SHA-256 digest.
    HashMismatch { expected: String, actual: String },
    /// A content-addressed object is missing or no longer matches its address.
    CorruptObject { digest: String, path: PathBuf },
    /// A numeric value cannot be represented by `SQLite` or the domain envelope.
    NumericOverflow,
}

impl Display for StoreError {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Database(_) => formatter.write_str("database operation failed"),
            Self::Io(_) => formatter.write_str("filesystem operation failed"),
            Self::Serialization(_) => formatter.write_str("stored JSON is invalid"),
            Self::CorruptEventStream { session_id } => {
                write!(formatter, "event stream {session_id} is corrupt")
            }
            Self::ConcurrencyConflict {
                session_id,
                expected,
                actual,
            } => write!(
                formatter,
                "event stream {session_id} expected version {expected} but found {actual}"
            ),
            Self::InvalidIdentifier => formatter.write_str("identifier is invalid"),
            Self::HashMismatch { expected, actual } => {
                write!(
                    formatter,
                    "expected digest {expected} but computed {actual}"
                )
            }
            Self::CorruptObject { digest, path } => write!(
                formatter,
                "content object {digest} at {} is missing or corrupt",
                path.display()
            ),
            Self::NumericOverflow => formatter.write_str("numeric value is out of range"),
        }
    }
}

impl Error for StoreError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            Self::Database(error) => Some(error),
            Self::Io(error) => Some(error),
            Self::Serialization(error) => Some(error),
            _ => None,
        }
    }
}

impl From<rusqlite::Error> for StoreError {
    fn from(error: rusqlite::Error) -> Self {
        Self::Database(error)
    }
}

impl From<std::io::Error> for StoreError {
    fn from(error: std::io::Error) -> Self {
        Self::Io(error)
    }
}

impl From<serde_json::Error> for StoreError {
    fn from(error: serde_json::Error) -> Self {
        Self::Serialization(error)
    }
}

/// Result type used by detailed local adapter APIs.
pub type StoreResult<T> = Result<T, StoreError>;
