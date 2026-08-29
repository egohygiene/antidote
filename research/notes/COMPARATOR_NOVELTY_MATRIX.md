# Comparator, evidence, and novelty matrix

**Status:** governed issue #34 research artifact; not canonical manuscript prose.
**Roadmap:** `ANT-Q02`; GitHub issue #34.
**Machine-readable source:**
[`comparator-novelty-matrix.json`](../sources/comparator-novelty-matrix.json).

## Result first

The broad Antidote novelty story does **not** survive primary-source review.
Closed-loop affective music, current-to-target trajectories, real-time
generation, smooth musical feedback, physiology-driven adaptation, personal
associations, and longitudinal within-person learning all have prior
precedents. The strongest threats are Daly et al. (2016), Ehrlich et al. (2019),
Janssen et al. (2012), AffectMachine-Classical (2023), and MindMelody v2
(2026).

What remains defensible is narrower and is still a **candidate combination**,
not an established novelty claim:

> Antidote is a proposed research instrument for making a person-and-moment
> audio hypothesis inspectable across consented context selection,
> user-extensible semantic intent, time-indexed planning, realized acoustic
> structure, perceived and felt response, and longitudinal within-person
> updating.

The bounded search did not find one evaluated system containing that complete
chain. “Did not find” is deliberately different from “does not exist.” Issue
#35 must decide whether this combination is specific and useful enough to freeze
as the paper's contribution boundary.

## Search and interpretation boundary

This dossier deep-reviewed the current MindMelody version and searched backward
and laterally through affective brain-computer music interfaces, personalized
affective players, state-to-target music systems, real-time affective
generators, music-based digital therapeutics, and field syntheses. Source
identity was checked against DOI/publisher, PubMed, or arXiv records through
2026-08-29.

This is not:

- an exhaustive systematic review;
- a patentability or freedom-to-operate opinion;
- evidence that an unreported capability is absent;
- a comparison of unpublished implementation details; or
- evidence that Antidote's proposed combination works.

The JSON matrix therefore uses `not-reported` for a capability not found in the
exact reviewed artifact. It never converts search absence into an existence
claim.

## Comparator map

| Comparator | Exact artifact | Strongest overlap | Important difference | Evidence boundary |
| --- | --- | --- | --- | --- |
| MindMelody | arXiv:2605.01235v2, revised 2026-05-16 | EEG state, semantic intervention plan, target trajectory, controllable generation, feedback | No durable personal semantic/context/provenance chain was found in v2 | Preprint; non-clinical pilot; pilot sample count not found |
| Daly aBCMI | J. Neural Eng. version of record, 2016, doi:10.1088/1741-2560/13/4/046022 | Current state, desired trajectory, algorithmic generation, multimodal sensing, longitudinal personal model | No user-extensible semantic language or modern consent projection was found | Eight completers; attrition, constrained generator, and signal limitations |
| Ehrlich closed-loop BCI | PLOS ONE version of record, 2019, doi:10.1371/journal.pone.0213516 | Continuous generated music, smooth control, subsecond EEG feedback, user calibration | No contextual memory or longitudinal intent-to-response record was found | Listener n=11; BCI pilot n=5; heterogeneous preliminary results |
| AffectMachine-Classical | Front. Psychol. version of record, 2023, doi:10.3389/fpsyg.2023.1158172 | Interpretable probability-space sculpting, real-time generation, predefined affect trajectory | Biofeedback and person-specific learning are proposed, not evaluated | n=26 evaluates communicated affect, not felt response or benefit |
| Personalized affective music player | UMUAI version of record, 2012, doi:10.1007/s11257-011-9107-7 | Current-to-goal selection, personal associations, physiology, multiweek personal model | Selects an existing library; no generated semantic journey | Three male participants; real-world but extremely small evaluation |
| BEAMERS | arXiv:2211.14609v1 | Desired emotion variation, EEG, response variability to the same song | Recommends songs; no continuous generation or provenance chain | Preprint; reported accuracy not independently reproduced here |
| LUCID study | PLOS ONE version of record, 2022, doi:10.1371/journal.pone.0259312 | Explicit current mood, calm target, iso-principle journey, preference-informed sequence | Single preplanned curated sequence; no live sensing or generation | Open-label n=163; subgroup-dependent; commercial conflict disclosed |
| iHeartLift | IEEE EMBC version of record, 2011, doi:10.1109/IEMBS.2011.6090277 | Real-time physiological feedback controlling music tempo | Narrow tempo-focused playback rather than a semantic generator | Short conference report; broad benefit not established |
| Minimalist BCMI | arXiv:2606.01473v1 | Two-channel EEG, real-time stochastic music, explicit feature controls | No personal semantic/context/provenance layer | n=22; target and time effects null; person/trial variance dominates |

The complete 13-dimension assessment—including user agency, privacy,
provenance, longitudinal learning, and clinical positioning—is preserved in the
machine-readable matrix. This compact table is a reading aid, not a substitute
for those governed cells.

## MindMelody dossier

### Architecture reviewed

MindMelody v2 connects:

1. real-time EEG processing;
2. a global valence/arousal state and local affect trajectory;
3. a Qwen2.5-7B retrieval-augmented planner over a music-intervention knowledge
   base;
4. a structured plan containing description, musical attributes, target tempo,
   texture density, section dynamics, and target affect trajectory;
5. a MusicGen-medium-based hierarchical controller generating ten-second
   audio; and
6. physiological and subjective feedback.

The architecture is therefore direct prior art for Antidote's broad “state →
semantic plan → generated music → response” loop. Calling MindMelody merely an
EEG music generator would understate the overlap.

### Evaluation reviewed

- EEG modeling uses the 32-participant DEAP dataset.
- The audio-control evaluation uses 2,000 MusicCaps clips labeled by three
  annotators; the paper reports inter-rater reliability of ICC 0.77.
- The paper reports a randomized within-subject comparison of human playlist,
  text-only, text plus static valence/arousal, and the full system.
- The methods visible in v2 do not clearly report the pilot participant count.
- The paper calls the evaluation a non-clinical pilot and defers larger,
  longer-term, and clinical protocols.
- A code release, detailed data-governance statement, and conventional ethics
  statement were not found in the reviewed artifact.

These are reporting observations about v2, not allegations that the underlying
work lacks those elements.

### What MindMelody removes from Antidote's novelty space

- a semantic bridge between inferred state and generation;
- an inspectable structured intervention plan;
- a local affective trajectory rather than only a destination label;
- controllable generation rather than playlist recommendation alone; and
- a physiological/subjective response loop.

### Candidate distinctions that remain unestablished

- user-authored and extensible personal semantic language;
- optional rather than mandatory physiological sensing;
- consent-scoped contextual projection from selected journal or session data;
- explicit separation of intended plan, measured acoustic realization,
  perceived emotion, felt response, helpfulness, and harm;
- append-only provenance for every transformation; and
- durable advisory within-person learning across changing moments.

Each phrase above is a candidate design distinction. None is proof of novelty,
efficacy, or implementation.

## Evidence-strength map

| Question | Strongest evidence in this set | What it permits | What it does not permit |
| --- | --- | --- | --- |
| Do closed-loop affective music systems predate Antidote? | Peer-reviewed Daly 2016, Ehrlich 2019, iHeartLift 2011 | Reject a first-system claim | Infer that all loops work |
| Can music be generated continuously from affect controls? | Peer-reviewed Ehrlich 2019 and AffectMachine 2023 | Treat continuous control and probability-space mapping as precedent | Infer felt emotion, helpfulness, or clinical benefit |
| Has within-person affective music learning been studied longitudinally? | Peer-reviewed Daly 2016 and Janssen 2012 | Reject broad first-personalized/first-longitudinal claims | Claim robust generalization from small samples |
| Has current-to-target personalized sequencing been evaluated clinically? | Open-label randomized Mallik and Russo 2022 | Treat current state, target, preference, and sequencing as precedent | Attribute effects to one component or generalize across severity groups |
| Do real-time EEG loops reliably track intentional emotion? | Minimalist BCMI v1 conflicts with optimistic technical assumptions | Preserve uncertainty, person correction, and nonmandatory sensing | Conclude that EEG can never be useful |
| Is music neurofeedback a settled intervention class? | Sayal et al. 2025 systematic review | Describe an active, heterogeneous field | Claim consensus success measures or efficacy |
| Are commercial music digital therapeutics established as effective? | Venkatesan et al. 2026 scoping review | State that products exist and evidence is limited | Call Antidote a validated digital therapeutic |

Evidence grade belongs to a particular claim. A peer-reviewed engineering
prototype may be strong evidence that an architecture existed and weak evidence
that it benefits a listener.

## Novelty decisions

### Rejected claims

The paper must not claim that Antidote is the first:

- closed-loop affective music system;
- current-state-to-desired-state music system;
- physiological music-feedback loop;
- real-time generative affective music system;
- system with smooth affective musical transitions;
- personalized or longitudinal affective music learner; or
- system with interpretable affect-to-music planning or controls.

### Narrowed claims

“Moment-specific personalization” is too broad. Earlier work conditions music
on current state, desired change, personal associations, and person-dependent
responses. If the phrase remains, it must refer to the complete governed chain,
not to state awareness alone.

“Interpretability” is also too broad. Earlier systems expose valence/arousal
mappings, musical parameters, and semantic intervention plans. Antidote's
candidate interpretation boundary is end-to-end inspectability: which context
was permitted, what the user asked for, how the request became a plan, what
audio was actually realized, what the person reported, and what—if anything—the
personal model proposes changing.

### Unresolved contribution candidates

1. **Governed end-to-end mapping:** consented context → explicit semantic intent
   → time-indexed plan → measured acoustic realization → separated perceived and
   felt response → provenance-linked update.
2. **User-extensible sonic language:** high-level meanings, metaphors,
   inclusions, exclusions, and corrections remain first-class records rather
   than disappearing into an opaque prompt.
3. **Agency under uncertainty:** passive observations remain optional,
   uncertain tailoring variables; the person can inspect, override, stop, and
   reject model updates.
4. **Moment-conditioned longitudinal inquiry:** the research object is not a
   person's fixed “best music,” but how response changes across person, moment,
   context, desired transition, and acoustic journey.

The value and novelty of this combination remain to be argued and tested.

## Figure-ready competing-systems map

The machine-readable dimensions support a reproducible literature figure with
four visual regions:

| Region | Systems | Shared emphasis |
| --- | --- | --- |
| Sensed-state generative loops | Daly aBCMI; Ehrlich BCI; Minimalist BCMI; MindMelody | Physiological state → generated music → feedback |
| Interpretable affective generators | AffectMachine-Classical; MindMelody | Human-readable affect/plan → controllable synthesis |
| Personalized selection and sequencing | AMP; BEAMERS; LUCID | Current or desired change → personal model → existing audio |
| Qualifying syntheses | Music in the Loop; MDT scoping review | Heterogeneity, limited outcome evidence, unresolved measurement |

Antidote should be drawn as a proposed overlay across these regions, with its
candidate governance chain labeled separately. It must not occupy an empty
“first ever” territory in the figure.

## Handoff to issue #35

Issue #35 should freeze contribution language only after accepting these
constraints:

- use “we propose,” “we formalize,” or “we implement” only when the repository
  status supports the verb;
- use “our bounded review did not identify” rather than “no prior system”;
- describe Antidote as a research instrument, not a therapy or digital
  therapeutic;
- state the candidate contribution as a combination and operational separation,
  not the invention of closed-loop personalization; and
- keep the central learnability hypothesis open until repeated-session evidence
  exists.
