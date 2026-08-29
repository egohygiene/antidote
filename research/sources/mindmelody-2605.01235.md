# MindMelody source record

## Verified metadata

| Field | Value |
| --- | --- |
| Title | MindMelody: A Closed-Loop EEG-Driven System for Personalized Music Intervention |
| Authors | Yimeng Zhang; Yueru Sun; Haoyu Gu; Zhanpeng Jin |
| Identifier | arXiv:2605.01235 |
| Primary category | cs.SD (Sound) |
| Version reviewed | v2 |
| Submitted | 2026-05-02 04:15:32 UTC |
| Revised | 2026-05-16 20:26:03 UTC |
| DOI | 10.48550/arXiv.2605.01235 |
| Primary source | https://arxiv.org/abs/2605.01235 |
| Metadata verified | 2026-08-26 |

## Relevance to Antidote

The preprint is a high-priority novelty comparator because it describes a
closed loop connecting EEG-derived affect, a semantic intervention plan,
controllable music generation, and updated physiological and subjective
feedback. Its semantic bridge and adaptive loop overlap with broad parts of the
Antidote design neighborhood.

The full issue #34 comparison rejects novelty claims based only on a semantic
bridge, target trajectory, controllable generation, or feedback. Candidate
distinctions that remain unresolved include a user-extensible sonic language,
consent-scoped context, separate intended/realized/perceived/felt records,
provenance, and durable within-person mapping that does not require EEG.

## Architecture reviewed

The reviewed v2 artifact describes:

1. real-time EEG processing into global valence/arousal and a local affect
   trajectory;
2. a Qwen2.5-7B retrieval-augmented planner using a music-intervention
   knowledge base described as approximately 1,000 entries;
3. a structured plan containing a description, musical attributes, target
   tempo, texture density, section dynamics, and target affect trajectory;
4. a MusicGen-medium 1.5B backbone with a hierarchical EEG controller; and
5. physiological and subjective feedback closing the proposed loop.

Generation is reported as fixed ten-second output on an NVIDIA A100. These
details make MindMelody a direct system comparator, not merely a motivating
example.

## Evaluation reviewed

- EEG modeling uses the 32-participant DEAP dataset.
- Music-control evaluation uses 2,000 MusicCaps clips labeled by three
  annotators; the paper reports ICC 0.77.
- The non-clinical pilot is described as randomized and within-subject, with
  human playlist, text-only, text plus static valence/arousal, and full-system
  conditions.
- Reported outcomes include mean-opinion, perceived-helpfulness, valence-change,
  and arousal-deviation measures.
- The pilot participant count was not found in the reviewed v2 methods.
- A code release, detailed data-governance statement, and conventional ethics
  statement were not found in the reviewed artifact.

“Not found” describes this review of v2. It does not establish that an element
does not exist in unpublished work or another artifact.

## Evidence boundary

The authors report control-adherence, emotional-alignment, and perceived-
helpfulness results from a non-clinical pilot. Those are claims of the cited
preprint and have not been independently reproduced here. The paper is prior
literature, not proof of Antidote efficacy, clinical validity, or novelty.

## Source claims assessed

- The paper describes a closed loop from EEG-derived affect through a semantic
  intervention plan and controllable music generation to physiological and
  subjective feedback.
- The semantic planner and target trajectory substantially overlap Antidote's
  broad architecture; those elements cannot support a first-system claim.
- The authors characterize their evaluation as a non-clinical pilot.
- The reported control-adherence, alignment, and helpfulness measures are
  findings of this preprint, not observations reproduced by Antidote.

## Limitations and unresolved questions

- The reviewed artifact is an arXiv preprint rather than a peer-reviewed
  clinical trial.
- The reviewed methods do not clearly report the pilot participant count;
  independent replication and clinical relevance are unresolved.
- The fixed ten-second generation setting does not evaluate a long-form,
  smoothly replanned listening journey.
- A durable within-person model across sessions, user-authored semantic
  language, consent-scoped contextual projection, and end-to-end provenance
  were not found in v2.
- No result establishes that its generated audio treats a condition or that
  EEG provides a universal objective representation of emotion.
- Novelty conclusions require comparison with additional adaptive and
  personalized music systems.

## Allowed manuscript use

MindMelody may be cited as adjacent prior art showing that the design
neighborhood—EEG-derived affect, semantic planning, controllable generation,
and feedback—is active. The manuscript may accurately attribute the preprint's
reported system design and non-clinical pilot findings while labeling their
source and review status.

## Prohibited manuscript use

Do not use this source as proof of Antidote's novelty, efficacy, clinical
validity, safety, generalizability, or the reliability of EEG emotion inference.

## Comparator disposition

The complete structured comparison is recorded in
[`comparator-novelty-matrix.json`](comparator-novelty-matrix.json) and the
governed narrative synthesis in
[`COMPARATOR_NOVELTY_MATRIX.md`](../notes/COMPARATOR_NOVELTY_MATRIX.md).
MindMelody rejects broad novelty claims about semantic planning, target
trajectories, controllable generation, and feedback. The narrower Antidote
combination remains unresolved rather than established.
