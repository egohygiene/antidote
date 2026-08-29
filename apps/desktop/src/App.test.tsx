import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

import { App } from "./App";
import type {
  CanonicalSession,
  DesktopSnapshot,
  SessionClient,
} from "./session-api";
import { normalizeCommandError } from "./session-api";

vi.mock("@tauri-apps/api/core", () => ({
  convertFileSrc: (path: string) => `asset://localhost/${path}`,
  invoke: vi.fn(),
}));

const worker = {
  adapter_id: "antidote.mock",
  adapter_version: "1.0.0",
  model_id: "synthetic-triangle",
  model_revision: "1",
  license: "MIT",
  device_class: "synthetic-cpu",
  network_access: false,
  duration_seconds_min: 10,
  duration_seconds_max: 30,
  controls: ["duration", "deterministic_seed"],
  restrictions: ["synthetic-test-output-only", "no-network-access"],
  visible_downgrades: [
    "The mock worker does not claim to realize felt-state intent.",
  ],
};

function session(): CanonicalSession {
  return {
    id: "session-synthetic-ui",
    version: 8,
    started_at: "2026-08-29T00:00:00Z",
    closed_at: null,
    consent_grants: {},
    working_projection: null,
    moment: null,
    journey: null,
    journey_history: [],
    generation: null,
    exposure: null,
    responses: {},
    safety_events: [],
    safety_halt_id: null,
  };
}

function snapshot(
  phase: DesktopSnapshot["phase"],
  canonicalSession: CanonicalSession | null = session(),
): DesktopSnapshot {
  return {
    session_id: canonicalSession?.id ?? null,
    phase,
    canonical_session: canonicalSession,
    worker,
    progress: { stage: "synthesizing", fraction: 0.5, elapsed_ms: 30 },
    generation_active: phase === "generating",
    cancellation_requested: false,
    recovery_required: false,
  };
}

const unusedClient = {} as SessionClient;

describe("Antidote desktop session experience", () => {
  it("keeps invalid consent from being expressible through the check-in form", () => {
    const markup = renderToStaticMarkup(
      <App
        client={unusedClient}
        initialSnapshot={snapshot("check_in", null)}
      />,
    );

    expect(markup).toContain("Session permission");
    expect(markup).toContain("consent_confirmed");
    expect(markup).toContain('required=""');
    expect(markup).toContain("may not learn, synchronize");
    expect(
      normalizeCommandError({
        code: "consent_required",
        message: "Review consent.",
        recoverable: true,
      }),
    ).toEqual({
      code: "consent_required",
      message: "Review consent.",
      recoverable: true,
    });
  });

  it("shows cancellation as a terminal record rather than a felt response", () => {
    const current = session();
    current.generation = {
      specification: generationSpec(),
      state: "cancelled",
      result: {
        ...generationResult(),
        status: "cancelled",
        artifacts: [],
      },
    };
    const markup = renderToStaticMarkup(
      <App
        client={unusedClient}
        initialSnapshot={snapshot("generation_failed", current)}
      />,
    );

    expect(markup).toContain("Generation cancelled");
    expect(markup).toContain("not interpreted as a negative response");
    expect(markup).toContain("begin another session");
  });

  it("makes cancellation and restart recovery visible during generation", () => {
    const current = session();
    current.generation = {
      specification: generationSpec(),
      state: "running",
      result: null,
    };
    const recovering = snapshot("generating", current);
    recovering.generation_active = false;
    recovering.recovery_required = true;
    const markup = renderToStaticMarkup(
      <App client={unusedClient} initialSnapshot={recovering} />,
    );

    expect(markup).toContain("desktop restarted");
    expect(markup).toContain("Mark interrupted generation as failed");
    expect(markup).toContain("progress");
  });

  it("renders a worker crash with no playable-output claim and a recovery path", () => {
    const current = session();
    current.generation = {
      specification: generationSpec(),
      state: "failed",
      result: {
        ...generationResult(),
        status: "failed",
        artifacts: [],
        warnings: ["No complete playable artifact was recorded."],
        failure: {
          code: "worker_failed",
          message: "The local synthetic generation attempt did not complete.",
          retryable: true,
        },
      },
    };
    const markup = renderToStaticMarkup(
      <App
        client={unusedClient}
        initialSnapshot={snapshot("generation_failed", current)}
      />,
    );

    expect(markup).toContain("Generation did not complete");
    expect(markup).toContain("No complete playable artifact");
    expect(markup).toContain("begin another session");
  });

  it("keeps adverse-response language, safety acknowledgement, and response separate", () => {
    const current = session();
    current.exposure = {
      id: "exposure-synthetic-ui",
      approval_id: "approval-synthetic-ui",
      artifact_sha256: "d".repeat(64),
      started_at: "2026-08-29T00:00:10Z",
      state: {
        stopped: {
          stopped_at: "2026-08-29T00:00:12Z",
          reason: "adverse_response",
        },
      },
    };
    current.safety_halt_id = "safety-synthetic-ui";
    current.safety_events = [
      {
        id: "safety-synthetic-ui",
        kind: "playback_stop",
        description: "playback stopped after an adverse response",
        observed_at: "2026-08-29T00:00:12Z",
      },
    ];
    const markup = renderToStaticMarkup(
      <App
        client={unusedClient}
        initialSnapshot={snapshot("response", current)}
      />,
    );

    expect(markup).toContain("safety event was preserved");
    expect(markup).toContain("does not provide crisis or clinical care");
    expect(markup).toContain("I have seen this record");
    expect(markup).toContain("Possible harm");
  });

  it("renders the happy-path completion without claiming automatic learning", () => {
    const current = session();
    current.responses = {
      "response-synthetic-ui": {
        schema_version: "1.0.0",
        id: "response-synthetic-ui",
        session_id: current.id,
        exposure_id: "exposure-synthetic-ui",
        observed_at: "2026-08-29T00:00:20Z",
        window: "immediate",
        felt_state: { description: "A synthetic, neutral response." },
        wanted_intensity: true,
        helpfulness: 0.5,
        resonance: 0.4,
        mismatch: 0.1,
        harm: 0,
        later_aftereffect_requested: true,
        allow_personal_model_update: false,
      },
    };
    const markup = renderToStaticMarkup(
      <App
        client={unusedClient}
        initialSnapshot={snapshot("complete", current)}
      />,
    );

    expect(markup).toContain("Session record complete");
    expect(markup).toContain("No personal model was updated");
    expect(markup).toContain("Later aftereffect intent");
    expect(markup).toContain("preserved");
  });
});

function generationSpec() {
  return {
    schema_version: "1.0.0" as const,
    id: "generation-spec-synthetic-ui",
    session_id: "session-synthetic-ui",
    journey_plan_id: "journey-synthetic-ui",
    journey_plan_hash: "c".repeat(64),
    adapter: { id: "antidote.mock", version: "1.0.0" },
    model: { id: "synthetic-triangle", revision: "1" },
    duration_seconds: 10,
    output: { format: "wav" as const, sample_rate_hz: 8000, channels: 1 },
    created_at: "2026-08-29T00:00:00Z",
  };
}

function generationResult() {
  return {
    schema_version: "1.0.0" as const,
    id: "generation-result-synthetic-ui",
    generation_spec_id: "generation-spec-synthetic-ui",
    status: "failed" as const,
    adapter: { id: "antidote.mock", version: "1.0.0" },
    model: { id: "synthetic-triangle", revision: "1" },
    code_revision: "synthetic-ui",
    device_class: "synthetic-cpu",
    elapsed_ms: 10,
    artifacts: [],
    warnings: [],
    failure: null,
  };
}
