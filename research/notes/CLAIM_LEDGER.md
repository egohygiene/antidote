# Claim ledger

**Status:** frozen manuscript claim contract for issue #35.
**Manuscript contract:**
[`paper/manuscript-contract.json`](../../paper/manuscript-contract.json).

This ledger governs what each evidence class may do in the first Antidote
design/protocol manuscript. A permitted section is not permission to strengthen
a statement: every use must remain within the evidence and wording boundary in
its row. New manuscript claims must enter this ledger before they enter prose.

## Sources and source syntheses

| ID | Class | Governed statement | Evidence | Permitted sections | Status and wording boundary |
| --- | --- | --- | --- | --- | --- |
| ANT-SRC-001 | Source | MindMelody v2 reports an EEG-to-affect-to-semantic-plan-to-music loop and a non-clinical pilot. | `mindmelody-2605.01235` source record. | Introduction; Related Work. | Verified reviewed preprint. Attribute findings to the authors; do not treat the pilot as Antidote evidence. |
| ANT-SRC-002 | Source synthesis | JITAI, MPC, POMDP, interactive-ML, controllable-music, adaptive-music, audio-rendering, local-first, event-sourcing, and provenance sources provide precedents for components of a two-rate generate-ahead architecture. | Issue #33 source records and architecture evidence map. | Related Work; System Design; Methods; Limitations. | Promoted architecture evidence. Name the transfer and non-transfer; it validates no affective or clinical outcome. |
| ANT-SRC-003 | Source synthesis | Closed-loop affective music, current-to-target trajectories, real-time generation, interpretable controls, physiology-driven adaptation, and longitudinal personalization all have prior precedents. | Issue #34 comparator matrix and governed source records. | Introduction; Related Work; Discussion; Conclusion. | Promoted comparison. Broad first-system claims are rejected. Search absence supports only bounded-review language. |

## Hypotheses and research questions

| ID | Class | Governed statement | Evidence | Permitted sections | Status and wording boundary |
| --- | --- | --- | --- | --- | --- |
| ANT-HYP-001 | Hypothesis | Repeated, provenance-linked records may reveal useful within-person and moment-conditioned relationships among semantic intent, acoustic realization, and self-reported response. | Conceptual model and unresolved contribution candidate from issue #34. | Introduction; Methods; Discussion; Conclusion as unanswered. | Open RQ3. Do not promise learnability, improved targeting, benefit, or generalization. |
| ANT-HYP-002 | Hypothesis | A person-correctable state belief, short planning horizon, typed semantic mixins, verified generate-ahead buffer, and deterministic renderer may support responsive journeys without abrupt playback changes. | Issue #33 architecture synthesis only. | System Design; Methods; Discussion; Limitations. | Open and not implemented end to end. “May support” does not mean seamless, stable, safe, or beneficial. |
| ANT-HYP-003 | Hypothesis | Separating intended controls, measured realization, perceived expression, felt response, immediate usefulness or harm, and aftereffect may make later within-person evidence more interpretable. | Epistemology, ontology, measurement literature, and design rationale. | Introduction; Methods; Discussion; Conclusion as prospective. | Open methodological hypothesis. Separation reduces conflation; it does not remove measurement error or establish validity. |

## Observations

| ID | Class | Governed statement | Evidence | Permitted sections | Status and wording boundary |
| --- | --- | --- | --- | --- | --- |
| ANT-OBS-001 | Observation | The researcher experienced one intentional generative-audio session as strongly cathartic. | Preserved bootstrap snapshot; no formal protocol. | Introduction as origin only; Limitations. | Hypothesis-generating self-report. Never a Results entry, efficacy signal, mechanism, or generalizable finding. |
| ANT-OBS-002 | Observation | The repository implements a reproducible publication workspace and an executable synthetic session through a rule-guided local core and deterministic mock worker; real-model audio, full provenance export, and a formal study remain incomplete. | Checked-in source, tests, `SYSTEM.md`, and `ARCHITECTURE.md` at the reviewed revision. | System Design; Results as technical status only; Availability. | Repository observation. Re-check against the source revision before publication; synthetic execution is not participant evidence. |

## Interpretations

| ID | Class | Governed statement | Evidence | Permitted sections | Status and wording boundary |
| --- | --- | --- | --- | --- | --- |
| ANT-INT-001 | Interpretation | The complete governed chain may be a useful research-system contribution because the bounded review did not identify it in one evaluated system. | Issue #34 comparator and novelty matrix. | Introduction; Related Work; Discussion; Conclusion. | Accepted contribution rationale, not proof of global novelty. Use “our bounded review did not identify,” never “no prior system.” |
| ANT-INT-002 | Interpretation | End-to-end inspectability is a more defensible Antidote boundary than interpretability of an affect label, control, or semantic plan alone. | Prior interpretable systems plus Antidote ontology and governance design. | Introduction; Related Work; Discussion. | Accepted design interpretation. Inspectability does not guarantee understanding, correctness, consent, safety, or benefit. |

## Accepted design/protocol claims

| ID | Class | Governed statement | Evidence | Permitted sections | Status and wording boundary |
| --- | --- | --- | --- | --- | --- |
| ANT-CLM-001 | Claim | Antidote formalizes an end-to-end governed mapping across consented context, user-extensible semantic intent, time-indexed planning, realized acoustic structure, separated perceived and felt response, provenance, and advisory within-person updating. | Issue #34 matrix plus `ONTOLOGY.md`, `PERSONAL_MODEL.md`, and the manuscript contract. | Introduction; Related Work; System Design; Discussion; Conclusion. | Accepted combination claim. The combination is proposed and formalized; its novelty, learnability, and benefit remain unresolved. |
| ANT-CLM-002 | Claim | Passive observations, when used, remain optional and uncertain tailoring variables that a person can inspect and correct; they are not objective emotion or need. | De Angel et al.; D'Amelio et al.; JITAI record; architecture map; AI constitution. | System Design; Methods; Limitations. | Accepted design constraint; study behavior and measurement validity remain unverified. |
| ANT-CLM-003 | Claim | The Antidote evidence model keeps requested semantic intent, planned controls, measured acoustic realization, perceived expression, felt response, immediate usefulness or harm, later aftereffect, and clinical outcome non-interchangeable. | `EPISTEMOLOGY.md`, `ONTOLOGY.md`, and the manuscript contract. | Introduction; System Design; Methods; Results; Discussion; Limitations; Conclusion. | Accepted methodological claim about the framework, not proof that its measures are valid or complete. |
| ANT-CLM-004 | Claim | The v0 authority model requires explicit human approval for context, plan acceptance, generation, playback, retention, export, and any personal-model update, with stop and correction preserved. | `AI_CONSTITUTION.md`, `PERSONAL_MODEL.md`, contracts, and checked-in mock implementation evidence. | System Design; Methods; Limitations; Availability. | Accepted design rule; distinguish enforced mock paths from proposed real-model and study behavior. |
| ANT-CLM-005 | Claim | Antidote proposes a two-rate architecture separating uncertain, inspectable deliberation from deterministic audio rendering, using explicit generation deadlines and independently governed semantic and waveform continuity. | Issue #33 architecture dossier and evidence map. | Related Work; System Design; Discussion; Limitations; Conclusion. | Accepted proposed architecture claim. Do not imply a validated controller, hard-real-time generator, exact adherence, or beneficial response. |

## Unresolved claim candidates

| ID | Class | Candidate statement | Evidence | Permitted sections | Status and wording boundary |
| --- | --- | --- | --- | --- | --- |
| ANT-CAN-001 | Claim candidate | The complete governed chain constitutes a novel research-system combination. | Issue #34 did not identify the complete chain in one evaluated system. | Introduction; Related Work; Discussion, only as an explicitly qualified candidate. | Unresolved. The manuscript may say the combination “may constitute” a contribution or that the bounded review “did not identify” it; it may not assert global novelty. |

## Rejected and prohibited claims

| ID | Class | Prohibited statement | Evidence | Applies to | Status |
| --- | --- | --- | --- | --- | --- |
| ANT-NEG-001 | Rejected claim | Antidote is the first closed-loop, current-to-target, real-time generative, physiologically adaptive, interpretable, or longitudinally personalized affective music system. | Issue #34 novelty decisions and prior systems. | Entire manuscript and all visuals. | Rejected by prior work. |
| ANT-NEG-002 | Rejected claim | Antidote, generated audio, semantic controls, a particular acoustic parameter, auditory beats, or the proposed controller treats a condition, guarantees a state transition, or produces a specific neurological mechanism. | Scientific boundaries, source limitations, and absence of qualifying Antidote evidence. | Entire manuscript and all visuals. | Prohibited without a materially different evidence and review gate. |
| ANT-NEG-003 | Rejected claim | Provenance, local-first execution, consent records, or inspectability prove truth, privacy, ownership, meaningful consent, safety, or benefit. | Architecture and provenance source limitations. | Entire manuscript and all visuals. | Category error; prohibited. |
| ANT-NEG-004 | Rejected claim | A synthetic fixture, mock audio artifact, repository test, originating experience, or unrun analysis is a human outcome result. | Epistemology and protocol boundary. | Results; Discussion; Abstract; Conclusion. | Prohibited evidence promotion. |

## Promotion rule

A new or stronger statement requires all of the following in one reviewable
change:

1. a stable ledger ID and evidence class;
2. the exact governed source, observation, or repository revision;
3. permitted sections and prohibited inferences;
4. wording no stronger than the evidence;
5. reconciliation with the manuscript contract and affected section; and
6. a recorded downgrade or rejection path when review does not support it.
