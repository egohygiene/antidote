# antidote-audio

Workspace scaffold for planned Rust ports and adapters for validated audio artifacts, deliberate
preview and playback, persistent stop and cancellation behavior, optional
transparent processing, waveform/metadata extraction, and export. Issue #21
owns implementation.

The first desktop implementation may use Web Audio through the Tauri webview.
CPAL or Rodio remains a fallback only if measured cross-platform behavior
requires native playback. Two engines should not be maintained without evidence.
