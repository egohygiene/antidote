use std::fmt::Write as _;
use std::fs::{self, File, OpenOptions};
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};

use antidote_core::{ArtifactStorePort, PortFailure};
use sha2::{Digest, Sha256};

use crate::{StoreError, StoreResult};

static TEMPORARY_COUNTER: AtomicU64 = AtomicU64::new(0);

/// Metadata returned after an object is durably placed by content digest.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct StoredObject {
    /// Lowercase SHA-256 digest used as the object address.
    pub sha256: String,
    /// Final object path below the configured root.
    pub path: PathBuf,
    /// Exact byte count stored.
    pub byte_length: u64,
    /// Whether this call created the object rather than finding identical content.
    pub created: bool,
}

/// Atomic content-addressed filesystem for artifacts or classified payloads.
#[derive(Debug, Clone)]
pub struct ContentAddressedStore {
    root: PathBuf,
}

impl ContentAddressedStore {
    /// Open one object namespace and remove abandoned temporary writes.
    ///
    /// # Errors
    ///
    /// Returns a filesystem failure when the root cannot be created, inspected,
    /// or cleaned.
    pub fn open(root: impl AsRef<Path>) -> StoreResult<Self> {
        let root = root.as_ref().to_path_buf();
        fs::create_dir_all(&root)?;
        let store = Self { root };
        store.remove_abandoned_temporary_files()?;
        Ok(store)
    }

    /// Return the configured namespace root.
    #[must_use]
    pub fn root(&self) -> &Path {
        &self.root
    }

    /// Atomically store bytes at their computed SHA-256 address.
    ///
    /// # Errors
    ///
    /// Returns a filesystem or integrity failure. Existing objects are verified
    /// before they are reused.
    pub fn put(&self, bytes: &[u8]) -> StoreResult<StoredObject> {
        let digest = sha256(bytes);
        self.put_expected(&digest, bytes)
    }

    /// Atomically store bytes only when they match an expected SHA-256 address.
    ///
    /// # Errors
    ///
    /// Returns [`StoreError::HashMismatch`] before the final object is changed,
    /// or a filesystem/integrity failure.
    pub fn put_expected(&self, expected_sha256: &str, bytes: &[u8]) -> StoreResult<StoredObject> {
        require_sha256(expected_sha256)?;
        let actual = sha256(bytes);
        if actual != expected_sha256 {
            return Err(StoreError::HashMismatch {
                expected: expected_sha256.to_owned(),
                actual,
            });
        }

        let final_path = self.path_for(expected_sha256)?;
        let byte_length = u64::try_from(bytes.len()).map_err(|_| StoreError::NumericOverflow)?;
        if final_path.exists() {
            self.verify_detailed(expected_sha256)?;
            return Ok(StoredObject {
                sha256: expected_sha256.to_owned(),
                path: final_path,
                byte_length,
                created: false,
            });
        }

        let parent = final_path.parent().ok_or(StoreError::InvalidIdentifier)?;
        fs::create_dir_all(parent)?;
        let temporary_path = Self::temporary_path(parent);
        let write_result = (|| -> StoreResult<()> {
            let mut file = OpenOptions::new()
                .create_new(true)
                .write(true)
                .open(&temporary_path)?;
            file.write_all(bytes)?;
            file.sync_all()?;
            drop(file);
            match fs::hard_link(&temporary_path, &final_path) {
                Ok(()) => {
                    fs::remove_file(&temporary_path)?;
                    Ok(())
                }
                Err(_error) if final_path.exists() => {
                    fs::remove_file(&temporary_path)?;
                    self.verify_detailed(expected_sha256)
                }
                Err(error) => Err(StoreError::Io(error)),
            }
        })();
        if write_result.is_err() && temporary_path.exists() {
            let _ = fs::remove_file(&temporary_path);
        }
        write_result?;
        sync_directory(parent)?;

        Ok(StoredObject {
            sha256: expected_sha256.to_owned(),
            path: final_path,
            byte_length,
            created: true,
        })
    }

    /// Read and verify one addressed object.
    ///
    /// # Errors
    ///
    /// Returns an integrity error when content is absent or mismatched.
    pub fn read(&self, digest: &str) -> StoreResult<Vec<u8>> {
        let path = self.path_for(digest)?;
        let mut bytes = Vec::new();
        File::open(&path)
            .and_then(|mut file| file.read_to_end(&mut bytes))
            .map_err(|_| StoreError::CorruptObject {
                digest: digest.to_owned(),
                path: path.clone(),
            })?;
        let actual = sha256(&bytes);
        if actual != digest {
            return Err(StoreError::CorruptObject {
                digest: digest.to_owned(),
                path,
            });
        }
        Ok(bytes)
    }

    /// Verify one addressed object without returning private content.
    ///
    /// # Errors
    ///
    /// Returns an integrity error when content is absent or mismatched.
    pub fn verify_detailed(&self, digest: &str) -> StoreResult<()> {
        self.read(digest).map(|_| ())
    }

    /// Resolve an object address to its deterministic path.
    ///
    /// # Errors
    ///
    /// Returns [`StoreError::InvalidIdentifier`] for a malformed digest.
    pub fn path_for(&self, digest: &str) -> StoreResult<PathBuf> {
        require_sha256(digest)?;
        Ok(self.root.join(&digest[..2]).join(digest))
    }

    fn temporary_path(parent: &Path) -> PathBuf {
        let counter = TEMPORARY_COUNTER.fetch_add(1, Ordering::Relaxed);
        parent.join(format!(".antidote-tmp-{}-{counter}", std::process::id()))
    }

    fn remove_abandoned_temporary_files(&self) -> StoreResult<()> {
        let mut directories = vec![self.root.clone()];
        while let Some(directory) = directories.pop() {
            for entry in fs::read_dir(directory)? {
                let entry = entry?;
                let file_type = entry.file_type()?;
                if file_type.is_dir() {
                    directories.push(entry.path());
                } else if entry
                    .file_name()
                    .to_str()
                    .is_some_and(|name| name.starts_with(".antidote-tmp-"))
                {
                    fs::remove_file(entry.path())?;
                }
            }
        }
        Ok(())
    }
}

impl ArtifactStorePort for ContentAddressedStore {
    fn verify(&self, artifact_sha256: &str) -> Result<(), PortFailure> {
        self.verify_detailed(artifact_sha256)
            .map_err(|_| PortFailure::new("artifact_verify"))
    }
}

pub(crate) fn sha256(bytes: &[u8]) -> String {
    let digest = Sha256::digest(bytes);
    let mut encoded = String::with_capacity(64);
    for byte in digest {
        write!(&mut encoded, "{byte:02x}").expect("writing to a String cannot fail");
    }
    encoded
}

pub(crate) fn require_sha256(value: &str) -> StoreResult<()> {
    if value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        Ok(())
    } else {
        Err(StoreError::InvalidIdentifier)
    }
}

fn sync_directory(path: &Path) -> StoreResult<()> {
    File::open(path)?.sync_all()?;
    Ok(())
}
