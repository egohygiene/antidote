import {
  type FormEvent,
  type ReactNode,
  type RefObject,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import type { JourneyPlanStage } from "./generated/contracts";
import {
  type DesktopCommandError,
  type DesktopPhase,
  type DesktopSnapshot,
  type JourneyRevisionInput,
  type SessionClient,
  normalizeCommandError,
  playableArtifactUrl,
  tauriSessionClient,
} from "./session-api";

const phaseLabels: Record<DesktopPhase, string> = {
  check_in: "Check in",
  context_review: "Review context",
  journey_review: "Shape journey",
  generation_review: "Review generation",
  generating: "Generate",
  generation_failed: "Recover",
  ready_to_listen: "Listen",
  listening: "Listen",
  response: "Respond",
  complete: "Complete",
};

const journeySteps = [
  "check_in",
  "context_review",
  "journey_review",
  "generation_review",
  "generating",
  "ready_to_listen",
  "response",
  "complete",
] as const;

interface AppProps {
  client?: SessionClient;
  initialSnapshot?: DesktopSnapshot;
}

export function App({
  client = tauriSessionClient,
  initialSnapshot,
}: AppProps) {
  const [snapshot, setSnapshot] = useState<DesktopSnapshot | null>(
    initialSnapshot ?? null,
  );
  const [error, setError] = useState<DesktopCommandError | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const screenTitle = useRef<HTMLHeadingElement>(null);
  const audio = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    if (initialSnapshot !== undefined) {
      return;
    }
    void client
      .snapshot()
      .then(setSnapshot)
      .catch((reason: unknown) => setError(normalizeCommandError(reason)));
  }, [client, initialSnapshot]);

  useEffect(() => {
    screenTitle.current?.focus();
  }, [snapshot?.phase]);

  useEffect(() => {
    if (snapshot?.phase !== "generating") {
      return;
    }
    const timer = window.setInterval(() => {
      void client
        .snapshot()
        .then(setSnapshot)
        .catch(() => undefined);
    }, 300);
    return () => window.clearInterval(timer);
  }, [client, snapshot?.phase]);

  const artifactUrl = useMemo(
    () => (snapshot === null ? null : playableArtifactUrl(snapshot)),
    [snapshot],
  );

  async function perform(
    label: string,
    action: () => Promise<DesktopSnapshot>,
  ) {
    setBusy(label);
    setError(null);
    try {
      setSnapshot(await action());
    } catch (reason) {
      setError(normalizeCommandError(reason));
    } finally {
      setBusy(null);
    }
  }

  async function beginGeneration(simulation: "normal" | "crash") {
    setBusy("Approving the immutable request");
    setError(null);
    try {
      setSnapshot(await client.approveGeneration());
      setBusy("Generating synthetic audio");
      setSnapshot(await client.runGeneration(simulation));
    } catch (reason) {
      setError(normalizeCommandError(reason));
      try {
        setSnapshot(await client.snapshot());
      } catch {
        // Preserve the actionable command error when the host is unavailable.
      }
    } finally {
      setBusy(null);
    }
  }

  async function startPlayback() {
    await perform("Authorizing playback", async () => {
      const next = await client.startPlayback();
      window.setTimeout(() => {
        void audio.current?.play().catch(() => {
          void client.stopPlayback("playback_failure").then(setSnapshot);
        });
      }, 0);
      return next;
    });
  }

  async function stopPlayback(
    reason:
      "person_stopped" | "completed" | "playback_failure" | "adverse_response",
  ) {
    audio.current?.pause();
    await perform("Stopping playback", () => client.stopPlayback(reason));
  }

  const phase = snapshot?.phase ?? "check_in";

  return (
    <>
      <a className="skip-link" href="#session-screen">
        Skip to session
      </a>
      <header className="app-header">
        <div>
          <p className="eyebrow">Local research instrument · mock audio only</p>
          <h1>Antidote</h1>
        </div>
        <p className="boundary-note">
          This prototype explores interpretable audio journeys. It does not
          diagnose, treat, or predict how you will feel.
        </p>
      </header>

      <nav className="journey-nav" aria-label="Session progress">
        <ol>
          {journeySteps.map((step, index) => {
            const currentIndex = journeySteps.indexOf(
              phase === "generation_failed"
                ? "generating"
                : phase === "listening"
                  ? "ready_to_listen"
                  : phase,
            );
            return (
              <li
                className={index <= currentIndex ? "reached" : undefined}
                key={step}
                aria-current={index === currentIndex ? "step" : undefined}
              >
                <span>{index + 1}</span>
                {phaseLabels[step]}
              </li>
            );
          })}
        </ol>
      </nav>

      <main id="session-screen" aria-busy={busy !== null}>
        {error !== null && (
          <div className="notice error" role="alert">
            <strong>{error.message}</strong>
            <span>Reference: {error.code}</span>
          </div>
        )}
        {busy !== null && (
          <p className="notice working" role="status" aria-live="polite">
            {busy}…
          </p>
        )}

        {snapshot === null ? (
          <Screen title="Opening local session" titleRef={screenTitle}>
            <p>
              Loading the Rust-owned session projection. No generation or
              playback starts automatically.
            </p>
          </Screen>
        ) : (
          <SessionScreen
            snapshot={snapshot}
            client={client}
            titleRef={screenTitle}
            artifactUrl={artifactUrl}
            audioRef={audio}
            busy={busy !== null}
            perform={perform}
            beginGeneration={beginGeneration}
            startPlayback={startPlayback}
            stopPlayback={stopPlayback}
          />
        )}
      </main>
    </>
  );
}

interface SessionScreenProps {
  snapshot: DesktopSnapshot;
  client: SessionClient;
  titleRef: RefObject<HTMLHeadingElement | null>;
  artifactUrl: string | null;
  audioRef: RefObject<HTMLAudioElement | null>;
  busy: boolean;
  perform: (
    label: string,
    action: () => Promise<DesktopSnapshot>,
  ) => Promise<void>;
  beginGeneration: (simulation: "normal" | "crash") => Promise<void>;
  startPlayback: () => Promise<void>;
  stopPlayback: (
    reason:
      "person_stopped" | "completed" | "playback_failure" | "adverse_response",
  ) => Promise<void>;
}

function SessionScreen(props: SessionScreenProps) {
  switch (props.snapshot.phase) {
    case "check_in":
      return <CheckInScreen {...props} />;
    case "context_review":
      return <ContextReviewScreen {...props} />;
    case "journey_review":
      return <JourneyReviewScreen {...props} />;
    case "generation_review":
      return <GenerationReviewScreen {...props} />;
    case "generating":
      return <GeneratingScreen {...props} />;
    case "generation_failed":
      return <GenerationFailedScreen {...props} />;
    case "ready_to_listen":
    case "listening":
      return <ListeningScreen {...props} />;
    case "response":
      return <ResponseScreen {...props} />;
    case "complete":
      return <CompleteScreen {...props} />;
  }
}

function CheckInScreen({
  client,
  perform,
  titleRef,
  busy,
}: SessionScreenProps) {
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    void perform("Recording your check-in", () =>
      client.recordCheckIn({
        current_state: field(form, "current_state"),
        desired_direction: field(form, "desired_direction"),
        desired_transition: field(form, "desired_transition"),
        horizon_seconds: Number(field(form, "horizon_seconds")),
        inclusions: lines(field(form, "inclusions")),
        exclusions: lines(field(form, "exclusions")),
        optional_context: optionalField(form, "optional_context"),
        notes: optionalField(form, "notes"),
        consent_confirmed: form.get("consent_confirmed") === "on",
      }),
    );
  }

  return (
    <Screen
      title="What fits this moment?"
      titleRef={titleRef}
      intro="Describe only what feels useful now. You can create a journey without journal, therapy-chat, or historical context."
    >
      <form onSubmit={submit} className="session-form">
        <Field label="What is present right now?" htmlFor="current_state">
          <textarea
            id="current_state"
            name="current_state"
            required
            maxLength={2000}
            rows={3}
          />
        </Field>

        <div className="two-column">
          <Field label="Direction to explore" htmlFor="desired_direction">
            <select
              id="desired_direction"
              name="desired_direction"
              defaultValue="regulate"
            >
              <option value="stay_with">Stay with</option>
              <option value="soften">Soften</option>
              <option value="regulate">Regulate</option>
              <option value="uplift">Uplift</option>
              <option value="focus">Focus</option>
              <option value="release">Release</option>
              <option value="explore">Explore</option>
              <option value="other">Something else</option>
            </select>
          </Field>
          <Field label="Journey length" htmlFor="horizon_seconds">
            <select
              id="horizon_seconds"
              name="horizon_seconds"
              defaultValue="20"
            >
              <option value="10">10 seconds</option>
              <option value="20">20 seconds</option>
              <option value="30">30 seconds</option>
            </select>
          </Field>
        </div>

        <Field
          label="What would movement in that direction mean?"
          htmlFor="desired_transition"
        >
          <textarea
            id="desired_transition"
            name="desired_transition"
            required
            maxLength={2000}
            rows={3}
          />
        </Field>

        <div className="two-column">
          <Field
            label="Include, if it fits"
            hint="One phrase per line"
            htmlFor="inclusions"
          >
            <textarea id="inclusions" name="inclusions" rows={4} />
          </Field>
          <Field
            label="Avoid completely"
            hint="Exclusions are checked before positive preferences"
            htmlFor="exclusions"
          >
            <textarea id="exclusions" name="exclusions" rows={4} />
          </Field>
        </div>

        <Field
          label="Optional context for this session"
          hint="Manual text only in this MVP. It will be shown back exactly before planning."
          htmlFor="optional_context"
        >
          <textarea
            id="optional_context"
            name="optional_context"
            rows={3}
            maxLength={2000}
          />
        </Field>

        <Field label="Private session note (optional)" htmlFor="notes">
          <textarea id="notes" name="notes" rows={2} maxLength={4000} />
        </Field>

        <fieldset className="consent-card">
          <legend>Session permission</legend>
          <p>
            The local Rust core may retain this check-in for this session,
            project the optional text shown above, generate synthetic test
            audio, and retain your response. It may not learn, synchronize,
            publish, or use a real model.
          </p>
          <label className="check-row">
            <input type="checkbox" name="consent_confirmed" required />
            <span>I reviewed and authorize these exact local actions.</span>
          </label>
        </fieldset>

        <button className="primary" type="submit" disabled={busy}>
          Review what Antidote will use
        </button>
      </form>
    </Screen>
  );
}

function ContextReviewScreen({
  snapshot,
  client,
  perform,
  titleRef,
  busy,
}: SessionScreenProps) {
  const session = requiredSession(snapshot);
  const grant = Object.values(session.consent_grants)[0];
  const projection = session.working_projection;
  return (
    <Screen
      title="Review the exact working context"
      titleRef={titleRef}
      intro="Nothing here has reached the generator. This is the complete context projection available to the rule-guided planner."
    >
      <section className="context-sheet" aria-labelledby="projection-heading">
        <h3 id="projection-heading">Working projection</h3>
        {projection?.semantic_items.length ? (
          <ul className="semantic-items">
            {projection.semantic_items.map((item) => (
              <li key={item.id}>
                <span>{item.kind}</span>
                <p>{item.text}</p>
                <strong>{item.user_review}</strong>
              </li>
            ))}
          </ul>
        ) : (
          <p>
            No optional historical context was selected. Planning will use only
            the current check-in, desired transition, inclusions, and
            exclusions.
          </p>
        )}
      </section>

      <details>
        <summary>Inspect consent scope</summary>
        <dl className="metadata-grid">
          <div>
            <dt>Purposes</dt>
            <dd>{grant?.purposes.join(", ")}</dd>
          </div>
          <div>
            <dt>Actions</dt>
            <dd>{grant?.actions.join(", ")}</dd>
          </div>
          <div>
            <dt>Retention</dt>
            <dd>{grant?.retention.mode}</dd>
          </div>
          <div>
            <dt>Personal-model updates</dt>
            <dd>Not authorized</dd>
          </div>
        </dl>
      </details>

      <div className="action-row">
        <button
          type="button"
          className="primary"
          disabled={busy}
          onClick={() =>
            void perform("Building an inspectable draft", () =>
              client.proposeJourney(),
            )
          }
        >
          Use this projection to propose a journey
        </button>
      </div>
    </Screen>
  );
}

function JourneyReviewScreen({
  snapshot,
  client,
  perform,
  titleRef,
  busy,
}: SessionScreenProps) {
  const plan = requiredSession(snapshot).journey?.plan;
  if (plan === undefined) {
    return null;
  }
  const currentPlan = plan;

  function revise(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const input: JourneyRevisionInput = {
      strategy: field(form, "strategy"),
      stages: currentPlan.stages.map((_stage, index) => ({
        semantic_intent: lines(field(form, `semantic-${index}`)),
        tempo_bpm: optionalNumber(form, `tempo-${index}`),
        density: optionalNumber(form, `density-${index}`),
      })),
    };
    void perform("Saving an immutable revision", () =>
      client.reviseJourney(input),
    );
  }

  return (
    <Screen
      title="Shape the proposed journey"
      titleRef={titleRef}
      intro="This is a deterministic, editable instruction set—not a prediction, prescription, or promise of benefit."
    >
      <form onSubmit={revise} className="session-form">
        <Field label="Journey strategy" htmlFor="strategy">
          <textarea
            id="strategy"
            name="strategy"
            defaultValue={plan.strategy}
            rows={3}
            required
          />
        </Field>

        <div className="storyboard" aria-label="Editable journey stages">
          {plan.stages.map((stage, index) => (
            <StageEditor stage={stage} index={index} key={stage.id} />
          ))}
        </div>

        <details open>
          <summary>Why these choices?</summary>
          <ul className="derivation-list">
            {plan.derivations?.map((derivation) => (
              <li key={`${derivation.target}-${derivation.rule_id}`}>
                <strong>{humanizeTarget(derivation.target)}</strong>
                <p>{derivation.rationale}</p>
                <small>{derivation.uncertainty}</small>
              </li>
            ))}
          </ul>
        </details>

        <section className="safety-sheet" aria-labelledby="constraints-heading">
          <h3 id="constraints-heading">Visible constraints</h3>
          <ul>
            {plan.safety_constraints.map((constraint) => (
              <li key={constraint}>{constraint}</li>
            ))}
          </ul>
        </section>

        <div className="action-row split">
          <button type="submit" disabled={busy}>
            Save as a new revision
          </button>
          <button
            className="primary"
            type="button"
            disabled={busy}
            onClick={() =>
              void perform("Sealing the approved plan", () =>
                client.approveJourney(),
              )
            }
          >
            Approve this exact journey
          </button>
        </div>
      </form>
    </Screen>
  );
}

function StageEditor({
  stage,
  index,
}: {
  stage: JourneyPlanStage;
  index: number;
}) {
  return (
    <fieldset className="stage-card">
      <legend>
        Stage {index + 1}: {stage.role}
      </legend>
      <p className="stage-duration">{stage.duration_seconds} seconds</p>
      <Field label="Semantic intention" htmlFor={`semantic-${index}`}>
        <textarea
          id={`semantic-${index}`}
          name={`semantic-${index}`}
          defaultValue={stage.semantic_intent.join("\n")}
          rows={3}
          required
        />
      </Field>
      <div className="two-column compact">
        <Field label="Requested tempo (BPM)" htmlFor={`tempo-${index}`}>
          <input
            id={`tempo-${index}`}
            name={`tempo-${index}`}
            type="number"
            min="48"
            max="112"
            step="1"
            defaultValue={stage.acoustic_controls.tempo_bpm ?? ""}
          />
        </Field>
        <Field label="Requested density (0–0.65)" htmlFor={`density-${index}`}>
          <input
            id={`density-${index}`}
            name={`density-${index}`}
            type="number"
            min="0"
            max="0.65"
            step="0.05"
            defaultValue={stage.acoustic_controls.density ?? ""}
          />
        </Field>
      </div>
      <details>
        <summary>All requested acoustic controls</summary>
        <pre>{JSON.stringify(stage.acoustic_controls, null, 2)}</pre>
      </details>
    </fieldset>
  );
}

function GenerationReviewScreen({
  snapshot,
  titleRef,
  busy,
  beginGeneration,
}: SessionScreenProps) {
  const specification = requiredSession(snapshot).generation?.specification;
  if (specification === undefined) {
    return null;
  }
  return (
    <Screen
      title="Review the immutable generation request"
      titleRef={titleRef}
      intro="Generation still requires a separate approval. The worker receives the accepted journey plan—not unrestricted personal history."
    >
      <WorkerSummary snapshot={snapshot} />

      <section className="warning-sheet" aria-labelledby="downgrade-heading">
        <h3 id="downgrade-heading">Known mock limitations</h3>
        <ul>
          {snapshot.worker.visible_downgrades.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
      </section>

      <details>
        <summary>Inspect exact generation specification</summary>
        <pre>{JSON.stringify(specification, null, 2)}</pre>
      </details>

      <div className="action-row">
        <button
          className="primary"
          type="button"
          disabled={busy}
          onClick={() => void beginGeneration("normal")}
        >
          Approve and generate synthetic audio
        </button>
        <details className="test-controls">
          <summary>Test a failure path</summary>
          <p>This intentionally asks the mock worker to simulate a crash.</p>
          <button
            type="button"
            disabled={busy}
            onClick={() => void beginGeneration("crash")}
          >
            Simulate worker crash
          </button>
        </details>
      </div>
    </Screen>
  );
}

function GeneratingScreen({
  snapshot,
  client,
  perform,
  titleRef,
}: SessionScreenProps) {
  const percent = Math.round(snapshot.progress.fraction * 100);
  return (
    <Screen
      title="Generating locally"
      titleRef={titleRef}
      intro="The deterministic Python worker has no network access and no personal-history or database authority."
    >
      <div className="progress-card" role="status" aria-live="polite">
        <p>{humanizeTarget(snapshot.progress.stage)}</p>
        <progress value={snapshot.progress.fraction} max="1">
          {percent}%
        </progress>
        <span>{percent}%</span>
      </div>

      {snapshot.recovery_required ? (
        <div className="notice error">
          <p>
            The desktop restarted while this job was marked running. No output
            will be treated as complete until the interruption is classified.
          </p>
          <button
            type="button"
            onClick={() =>
              void perform("Recovering interrupted state", () =>
                client.recoverInterruptedGeneration(),
              )
            }
          >
            Mark interrupted generation as failed
          </button>
        </div>
      ) : (
        <button
          type="button"
          className="stop-control"
          disabled={snapshot.cancellation_requested}
          onClick={() =>
            void perform("Requesting cancellation", () =>
              client.cancelGeneration(),
            )
          }
        >
          {snapshot.cancellation_requested
            ? "Cancellation requested"
            : "Cancel generation"}
        </button>
      )}
    </Screen>
  );
}

function GenerationFailedScreen({
  snapshot,
  client,
  perform,
  titleRef,
}: SessionScreenProps) {
  const result = requiredSession(snapshot).generation?.result;
  const cancelled = result?.status === "cancelled";
  return (
    <Screen
      title={cancelled ? "Generation cancelled" : "Generation did not complete"}
      titleRef={titleRef}
      intro={
        cancelled
          ? "The cancellation is preserved as a terminal result, not interpreted as a negative response."
          : "No partial or failed output is presented as playable audio. Your check-in and approved plan remain inspectable."
      }
    >
      <section className="failure-sheet" aria-labelledby="failure-heading">
        <h3 id="failure-heading">What happened</h3>
        <p>
          {result?.failure?.message ??
            "The job ended without a complete artifact."}
        </p>
        {result?.warnings.length ? (
          <ul>
            {result.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        ) : null}
      </section>
      <button
        type="button"
        onClick={() =>
          void perform("Closing this preserved session", () =>
            client.closeSession(),
          )
        }
      >
        Preserve this record and begin another session
      </button>
    </Screen>
  );
}

function ListeningScreen({
  snapshot,
  titleRef,
  artifactUrl,
  audioRef,
  startPlayback,
  stopPlayback,
}: SessionScreenProps) {
  const playing = snapshot.phase === "listening";
  return (
    <Screen
      title={
        playing ? "Synthetic preview playing" : "Your mock artifact is ready"
      }
      titleRef={titleRef}
      intro="Playback never starts automatically. This deterministic tone is test output, not therapeutic music."
    >
      {artifactUrl === null ? (
        <p className="notice error" role="alert">
          The canonical result has no verified audio path.
        </p>
      ) : (
        <audio
          ref={audioRef}
          src={artifactUrl}
          preload="metadata"
          onEnded={() => void stopPlayback("completed")}
          aria-label="Generated synthetic Antidote preview"
        />
      )}

      {!playing ? (
        <button
          type="button"
          className="primary"
          disabled={artifactUrl === null}
          onClick={() => void startPlayback()}
        >
          Start deliberate playback
        </button>
      ) : (
        <div
          className="persistent-controls"
          aria-label="Playback safety controls"
        >
          <button
            type="button"
            className="stop-control"
            onClick={() => void stopPlayback("person_stopped")}
          >
            Stop playback
          </button>
          <button
            type="button"
            className="adverse-control"
            onClick={() => void stopPlayback("adverse_response")}
          >
            Stop — this may be an adverse response
          </button>
        </div>
      )}
    </Screen>
  );
}

function ResponseScreen({
  snapshot,
  client,
  perform,
  titleRef,
  busy,
}: SessionScreenProps) {
  const session = requiredSession(snapshot);
  const safetyEvent = session.safety_halt_id
    ? session.safety_events.find((event) => event.id === session.safety_halt_id)
    : undefined;

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    void perform("Recording your response separately", () =>
      client.recordResponse({
        felt_state: field(form, "felt_state"),
        wanted_intensity: optionalBoolean(form, "wanted_intensity"),
        helpfulness: optionalNumber(form, "helpfulness"),
        resonance: optionalNumber(form, "resonance"),
        mismatch: optionalNumber(form, "mismatch"),
        harm: optionalNumber(form, "harm"),
        stopped_early: form.get("stopped_early") === "on",
        notes: optionalField(form, "response_notes"),
        later_aftereffect_requested:
          form.get("later_aftereffect_requested") === "on",
      }),
    );
  }

  return (
    <Screen
      title="What actually happened for you?"
      titleRef={titleRef}
      intro="A strong response is not automatically good or bad. Your interpretation, mismatch, usefulness, and possible harm remain separate observations."
    >
      {safetyEvent !== undefined && (
        <section className="adverse-sheet" role="alert">
          <h3>Playback was stopped and a safety event was preserved</h3>
          <p>{safetyEvent.description}</p>
          <p>
            Antidote does not provide crisis or clinical care. Choose what feels
            safe, step away from the prototype, and seek appropriate human help
            if needed.
          </p>
          <button
            type="button"
            onClick={() =>
              void perform("Acknowledging the visible safety record", () =>
                client.acknowledgeSafetyEvent(),
              )
            }
          >
            I have seen this record
          </button>
        </section>
      )}

      <form onSubmit={submit} className="session-form">
        <Field label="Describe the felt response" htmlFor="felt_state">
          <textarea
            id="felt_state"
            name="felt_state"
            rows={4}
            maxLength={4000}
            required
          />
        </Field>
        <Field label="Was the intensity wanted?" htmlFor="wanted_intensity">
          <select id="wanted_intensity" name="wanted_intensity" defaultValue="">
            <option value="">Not sure / prefer not to say</option>
            <option value="true">Yes</option>
            <option value="false">No</option>
          </select>
        </Field>
        <div className="score-grid">
          <ScoreField name="helpfulness" label="Felt helpful" />
          <ScoreField name="resonance" label="Resonance" />
          <ScoreField name="mismatch" label="Mismatch" />
          <ScoreField name="harm" label="Possible harm" />
        </div>
        <label className="check-row">
          <input type="checkbox" name="stopped_early" />
          <span>I stopped earlier than intended</span>
        </label>
        <Field label="Anything else to preserve?" htmlFor="response_notes">
          <textarea
            id="response_notes"
            name="response_notes"
            rows={3}
            maxLength={8000}
          />
        </Field>
        <label className="check-row">
          <input type="checkbox" name="later_aftereffect_requested" />
          <span>
            Preserve my intent to optionally record a later aftereffect. This
            does not schedule, notify, or infer one.
          </span>
        </label>
        <button className="primary" type="submit" disabled={busy}>
          Record this immediate response
        </button>
      </form>
    </Screen>
  );
}

function CompleteScreen({
  snapshot,
  client,
  perform,
  titleRef,
}: SessionScreenProps) {
  const responses = Object.values(requiredSession(snapshot).responses);
  const response = responses.at(-1);
  return (
    <Screen
      title="Session record complete"
      titleRef={titleRef}
      intro="The plan, generated artifact, actual exposure, and your response remain separate in the local event record. No personal model was updated."
    >
      <section
        className="response-summary"
        aria-labelledby="response-summary-title"
      >
        <h3 id="response-summary-title">Your recorded interpretation</h3>
        <p>{response?.felt_state.description}</p>
        <dl className="metadata-grid">
          <div>
            <dt>Helpfulness</dt>
            <dd>{formatScore(response?.helpfulness)}</dd>
          </div>
          <div>
            <dt>Resonance</dt>
            <dd>{formatScore(response?.resonance)}</dd>
          </div>
          <div>
            <dt>Mismatch</dt>
            <dd>{formatScore(response?.mismatch)}</dd>
          </div>
          <div>
            <dt>Possible harm</dt>
            <dd>{formatScore(response?.harm)}</dd>
          </div>
        </dl>
        <p>
          Later aftereffect intent:{" "}
          {response?.later_aftereffect_requested
            ? "preserved"
            : "not requested"}
        </p>
      </section>
      <button
        type="button"
        onClick={() =>
          void perform("Closing the local session", () => client.closeSession())
        }
      >
        Finish and return to check-in
      </button>
    </Screen>
  );
}

function WorkerSummary({ snapshot }: { snapshot: DesktopSnapshot }) {
  const worker = snapshot.worker;
  return (
    <section className="worker-card" aria-labelledby="worker-heading">
      <div>
        <p className="eyebrow">Local worker</p>
        <h3 id="worker-heading">
          {worker.adapter_id} · {worker.model_id}
        </h3>
      </div>
      <dl className="metadata-grid">
        <div>
          <dt>Device</dt>
          <dd>{worker.device_class}</dd>
        </div>
        <div>
          <dt>Network</dt>
          <dd>{worker.network_access ? "Enabled" : "Disabled"}</dd>
        </div>
        <div>
          <dt>License</dt>
          <dd>{worker.license}</dd>
        </div>
        <div>
          <dt>Duration</dt>
          <dd>
            {worker.duration_seconds_min}–{worker.duration_seconds_max} seconds
          </dd>
        </div>
      </dl>
      <p>Declared controls: {worker.controls.join(", ")}</p>
      <p>Restrictions: {worker.restrictions.join(", ")}</p>
    </section>
  );
}

function Screen({
  title,
  titleRef,
  intro,
  children,
}: {
  title: string;
  titleRef: RefObject<HTMLHeadingElement | null>;
  intro?: string;
  children: ReactNode;
}) {
  return (
    <article className="screen-card">
      <header className="screen-heading">
        <h2 ref={titleRef} tabIndex={-1}>
          {title}
        </h2>
        {intro !== undefined && <p>{intro}</p>}
      </header>
      {children}
    </article>
  );
}

function Field({
  label,
  hint,
  htmlFor,
  children,
}: {
  label: string;
  hint?: string;
  htmlFor: string;
  children: ReactNode;
}) {
  return (
    <label className="field" htmlFor={htmlFor}>
      <span>{label}</span>
      {hint !== undefined && <small>{hint}</small>}
      {children}
    </label>
  );
}

function ScoreField({ name, label }: { name: string; label: string }) {
  return (
    <Field label={label} htmlFor={name} hint="Optional: 0 is none; 1 is high">
      <select id={name} name={name} defaultValue="">
        <option value="">Not recorded</option>
        <option value="0">0</option>
        <option value="0.25">0.25</option>
        <option value="0.5">0.5</option>
        <option value="0.75">0.75</option>
        <option value="1">1</option>
      </select>
    </Field>
  );
}

function requiredSession(snapshot: DesktopSnapshot) {
  if (
    snapshot.canonical_session === null ||
    snapshot.canonical_session === undefined
  ) {
    throw new Error("Canonical session projection is missing");
  }
  return snapshot.canonical_session;
}

function field(form: FormData, name: string): string {
  const value = form.get(name);
  return typeof value === "string" ? value : "";
}

function optionalField(form: FormData, name: string): string | null {
  const value = field(form, name).trim();
  return value === "" ? null : value;
}

function lines(value: string): Array<string> {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

function optionalNumber(form: FormData, name: string): number | null {
  const value = field(form, name).trim();
  return value === "" ? null : Number(value);
}

function optionalBoolean(form: FormData, name: string): boolean | null {
  const value = field(form, name);
  if (value === "true") {
    return true;
  }
  if (value === "false") {
    return false;
  }
  return null;
}

function humanizeTarget(value: string): string {
  return value.replaceAll("/", " ").replaceAll("_", " ").trim();
}

function formatScore(value: number | null | undefined): string {
  return value === null || value === undefined ? "Not recorded" : String(value);
}
