import { invoke } from "@tauri-apps/api/core";
import { useEffect, useState } from "react";

const boundaries = [
  "No real audio model is installed.",
  "No personal or clinical data is accepted by this scaffold.",
  "Generation, playback, and adaptation remain unavailable.",
] as const;

export function App() {
  const [hostStatus, setHostStatus] = useState("browser-preview");

  useEffect(() => {
    void invoke<string>("prototype_status")
      .then(setHostStatus)
      .catch(() => setHostStatus("browser-preview"));
  }, []);

  return (
    <main>
      <header>
        <p className="eyebrow">Local research instrument</p>
        <h1>Antidote</h1>
        <p className="lede">
          The workspace is ready for contract-tested implementation. The session
          experience itself is not implemented yet.
        </p>
      </header>

      <section aria-labelledby="status-title">
        <h2 id="status-title">Foundation status</h2>
        <dl>
          <div>
            <dt>Desktop host</dt>
            <dd>{hostStatus}</dd>
          </div>
          <div>
            <dt>Contract source</dt>
            <dd>JSON Schema v1</dd>
          </div>
          <div>
            <dt>Current roadmap gate</dt>
            <dd>ANT-Q03 mock vertical slice</dd>
          </div>
        </dl>
      </section>

      <section aria-labelledby="boundaries-title">
        <h2 id="boundaries-title">Current boundaries</h2>
        <ul>
          {boundaries.map((boundary) => (
            <li key={boundary}>{boundary}</li>
          ))}
        </ul>
      </section>
    </main>
  );
}
