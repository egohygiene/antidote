//! Tauri lifecycle and capability boundary for the Antidote desktop host.

mod session;

use session::{
    CheckInInput, DesktopCommandError, DesktopRuntime, DesktopSnapshot, GenerationSimulation,
    JourneyRevisionInput, ResponseInput,
};
use tauri::{Manager, State};

#[tauri::command]
fn prototype_status() -> &'static str {
    "mock-session-interface-v1"
}

#[tauri::command]
fn session_snapshot(
    state: State<'_, DesktopRuntime>,
) -> Result<DesktopSnapshot, DesktopCommandError> {
    state.snapshot()
}

#[tauri::command]
fn record_check_in(
    state: State<'_, DesktopRuntime>,
    input: CheckInInput,
) -> Result<DesktopSnapshot, DesktopCommandError> {
    state.record_check_in(input)
}

#[tauri::command]
fn propose_journey(
    state: State<'_, DesktopRuntime>,
) -> Result<DesktopSnapshot, DesktopCommandError> {
    state.propose_journey()
}

#[tauri::command]
fn revise_journey(
    state: State<'_, DesktopRuntime>,
    input: JourneyRevisionInput,
) -> Result<DesktopSnapshot, DesktopCommandError> {
    state.revise_journey(input)
}

#[tauri::command]
fn approve_journey(
    state: State<'_, DesktopRuntime>,
) -> Result<DesktopSnapshot, DesktopCommandError> {
    state.approve_journey()
}

#[tauri::command]
fn approve_generation(
    state: State<'_, DesktopRuntime>,
) -> Result<DesktopSnapshot, DesktopCommandError> {
    state.approve_generation()
}

#[tauri::command]
async fn run_generation(
    state: State<'_, DesktopRuntime>,
    simulation: GenerationSimulation,
) -> Result<DesktopSnapshot, DesktopCommandError> {
    let runtime = (*state).clone();
    tauri::async_runtime::spawn_blocking(move || runtime.run_generation(simulation))
        .await
        .map_err(|_| DesktopCommandError {
            code: "generation_task_failed",
            message: "The local generation task stopped unexpectedly. Recover the canonical session before continuing.",
            recoverable: true,
        })?
}

#[tauri::command]
fn cancel_generation(
    state: State<'_, DesktopRuntime>,
) -> Result<DesktopSnapshot, DesktopCommandError> {
    state.cancel_generation()
}

#[tauri::command]
fn recover_interrupted_generation(
    state: State<'_, DesktopRuntime>,
) -> Result<DesktopSnapshot, DesktopCommandError> {
    state.recover_interrupted_generation()
}

#[tauri::command]
fn start_playback(
    state: State<'_, DesktopRuntime>,
) -> Result<DesktopSnapshot, DesktopCommandError> {
    state.start_playback()
}

#[tauri::command]
fn stop_playback(
    state: State<'_, DesktopRuntime>,
    reason: antidote_core::ExposureStopReason,
) -> Result<DesktopSnapshot, DesktopCommandError> {
    state.stop_playback(reason)
}

#[tauri::command]
fn record_response(
    state: State<'_, DesktopRuntime>,
    input: ResponseInput,
) -> Result<DesktopSnapshot, DesktopCommandError> {
    state.record_response(input)
}

#[tauri::command]
fn acknowledge_safety_event(
    state: State<'_, DesktopRuntime>,
) -> Result<DesktopSnapshot, DesktopCommandError> {
    state.acknowledge_safety_event()
}

#[tauri::command]
fn close_session(state: State<'_, DesktopRuntime>) -> Result<DesktopSnapshot, DesktopCommandError> {
    state.close_session()
}

/// Start the local desktop host.
///
/// # Panics
///
/// Panics if Tauri cannot initialize or run the desktop event loop.
pub fn run() {
    tauri::Builder::default()
        .setup(|application| {
            let data_root = application.path().app_local_data_dir()?;
            let runtime = DesktopRuntime::open(data_root)
                .map_err(|error| std::io::Error::other(error.code))?;
            application.manage(runtime);
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            prototype_status,
            session_snapshot,
            record_check_in,
            propose_journey,
            revise_journey,
            approve_journey,
            approve_generation,
            run_generation,
            cancel_generation,
            recover_interrupted_generation,
            start_playback,
            stop_playback,
            record_response,
            acknowledge_safety_event,
            close_session,
        ])
        .run(tauri::generate_context!())
        .expect("failed to run Antidote desktop host");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn host_status_names_the_mock_session_interface() {
        assert_eq!(prototype_status(), "mock-session-interface-v1");
    }
}
