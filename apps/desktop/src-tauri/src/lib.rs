//! Tauri lifecycle and capability boundary for the Antidote desktop host.

#[tauri::command]
fn prototype_status() -> &'static str {
    "workspace-scaffolded"
}

/// Start the local desktop host.
///
/// # Panics
///
/// Panics if Tauri cannot initialize or run the desktop event loop.
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![prototype_status])
        .run(tauri::generate_context!())
        .expect("failed to run Antidote desktop host");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn host_status_is_explicitly_scaffolded() {
        assert_eq!(prototype_status(), "workspace-scaffolded");
    }
}
