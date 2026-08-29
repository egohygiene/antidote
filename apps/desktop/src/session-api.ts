import { convertFileSrc, invoke } from "@tauri-apps/api/core";

import type {
  ConsentGrant,
  GenerationResult,
  GenerationSpec,
  JourneyPlan,
  MomentContext,
  ResponseObservation,
  WorkingContextProjection,
} from "./generated/contracts";

export type DesktopPhase =
  | "check_in"
  | "context_review"
  | "journey_review"
  | "generation_review"
  | "generating"
  | "generation_failed"
  | "ready_to_listen"
  | "listening"
  | "response"
  | "complete";

export interface JourneyState {
  plan: JourneyPlan;
  approval:
    | "draft"
    | { approved: { consent_grant_id: string; approved_at: string } }
    | { rejected: { reason: string; rejected_at: string } }
    | {
        superseded: { replacement_plan_id: string; superseded_at: string };
      };
}

export interface GenerationJob {
  specification: GenerationSpec;
  state:
    | "requested"
    | "approved"
    | "running"
    | "generated"
    | "cancelled"
    | "partial"
    | "failed";
  consent_grant_id?: string | null;
  result?: GenerationResult | null;
}

export interface Exposure {
  id: string;
  approval_id: string;
  artifact_sha256: string;
  started_at: string;
  state:
    | "playing"
    | {
        stopped: {
          stopped_at: string;
          reason:
            | "person_stopped"
            | "completed"
            | "playback_failure"
            | "adverse_response";
        };
      };
}

export interface SafetyEvent {
  id: string;
  kind:
    | "distress"
    | "mismatch"
    | "adverse_response"
    | "exclusion"
    | "playback_stop"
    | "other";
  description: string;
  observed_at: string;
}

export interface CanonicalSession {
  id: string;
  version: number;
  started_at?: string | null;
  closed_at?: string | null;
  consent_grants: Record<string, ConsentGrant>;
  working_projection?: WorkingContextProjection | null;
  moment?: MomentContext | null;
  journey?: JourneyState | null;
  journey_history: Array<JourneyState>;
  generation?: GenerationJob | null;
  exposure?: Exposure | null;
  responses: Record<string, ResponseObservation>;
  safety_events: Array<SafetyEvent>;
  safety_halt_id?: string | null;
}

export interface WorkerCard {
  adapter_id: string;
  adapter_version: string;
  model_id: string;
  model_revision: string;
  license: string;
  device_class: string;
  network_access: boolean;
  duration_seconds_min: number;
  duration_seconds_max: number;
  controls: Array<string>;
  restrictions: Array<string>;
  visible_downgrades: Array<string>;
}

export interface GenerationProgress {
  stage: string;
  fraction: number;
  elapsed_ms: number;
}

export interface DesktopSnapshot {
  session_id?: string | null;
  phase: DesktopPhase;
  canonical_session?: CanonicalSession | null;
  worker: WorkerCard;
  progress: GenerationProgress;
  generation_active: boolean;
  cancellation_requested: boolean;
  recovery_required: boolean;
}

export interface DesktopCommandError {
  code: string;
  message: string;
  recoverable: boolean;
}

export interface CheckInInput {
  current_state: string;
  desired_direction: string;
  desired_transition: string;
  horizon_seconds: number;
  inclusions: Array<string>;
  exclusions: Array<string>;
  optional_context?: string | null;
  notes?: string | null;
  consent_confirmed: boolean;
}

export interface JourneyRevisionInput {
  strategy: string;
  stages: Array<{
    semantic_intent: Array<string>;
    tempo_bpm?: number | null;
    density?: number | null;
  }>;
}

export interface ResponseInput {
  felt_state: string;
  wanted_intensity?: boolean | null;
  helpfulness?: number | null;
  resonance?: number | null;
  mismatch?: number | null;
  harm?: number | null;
  stopped_early: boolean;
  notes?: string | null;
  later_aftereffect_requested: boolean;
}

export interface SessionClient {
  snapshot(): Promise<DesktopSnapshot>;
  recordCheckIn(input: CheckInInput): Promise<DesktopSnapshot>;
  proposeJourney(): Promise<DesktopSnapshot>;
  reviseJourney(input: JourneyRevisionInput): Promise<DesktopSnapshot>;
  approveJourney(): Promise<DesktopSnapshot>;
  approveGeneration(): Promise<DesktopSnapshot>;
  runGeneration(simulation: "normal" | "crash"): Promise<DesktopSnapshot>;
  cancelGeneration(): Promise<DesktopSnapshot>;
  recoverInterruptedGeneration(): Promise<DesktopSnapshot>;
  startPlayback(): Promise<DesktopSnapshot>;
  stopPlayback(
    reason:
      "person_stopped" | "completed" | "playback_failure" | "adverse_response",
  ): Promise<DesktopSnapshot>;
  recordResponse(input: ResponseInput): Promise<DesktopSnapshot>;
  acknowledgeSafetyEvent(): Promise<DesktopSnapshot>;
  closeSession(): Promise<DesktopSnapshot>;
}

export const tauriSessionClient: SessionClient = {
  snapshot: () => invoke<DesktopSnapshot>("session_snapshot"),
  recordCheckIn: (input) =>
    invoke<DesktopSnapshot>("record_check_in", { input }),
  proposeJourney: () => invoke<DesktopSnapshot>("propose_journey"),
  reviseJourney: (input) =>
    invoke<DesktopSnapshot>("revise_journey", { input }),
  approveJourney: () => invoke<DesktopSnapshot>("approve_journey"),
  approveGeneration: () => invoke<DesktopSnapshot>("approve_generation"),
  runGeneration: (simulation) =>
    invoke<DesktopSnapshot>("run_generation", { simulation }),
  cancelGeneration: () => invoke<DesktopSnapshot>("cancel_generation"),
  recoverInterruptedGeneration: () =>
    invoke<DesktopSnapshot>("recover_interrupted_generation"),
  startPlayback: () => invoke<DesktopSnapshot>("start_playback"),
  stopPlayback: (reason) =>
    invoke<DesktopSnapshot>("stop_playback", { reason }),
  recordResponse: (input) =>
    invoke<DesktopSnapshot>("record_response", { input }),
  acknowledgeSafetyEvent: () =>
    invoke<DesktopSnapshot>("acknowledge_safety_event"),
  closeSession: () => invoke<DesktopSnapshot>("close_session"),
};

export function playableArtifactUrl(snapshot: DesktopSnapshot): string | null {
  const artifact =
    snapshot.canonical_session?.generation?.result?.artifacts.find(
      (candidate) => candidate.kind === "audio",
    );
  return artifact === undefined ? null : convertFileSrc(artifact.path);
}

export function normalizeCommandError(error: unknown): DesktopCommandError {
  if (
    typeof error === "object" &&
    error !== null &&
    "code" in error &&
    "message" in error
  ) {
    const candidate = error as Partial<DesktopCommandError>;
    return {
      code: String(candidate.code),
      message: String(candidate.message),
      recoverable: candidate.recoverable !== false,
    };
  }
  return {
    code: "desktop_unavailable",
    message:
      "The Tauri host is unavailable. Launch the desktop application to run a local session.",
    recoverable: true,
  };
}
