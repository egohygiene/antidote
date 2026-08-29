# Mustango source record

## Verified metadata

| Field | Value |
| --- | --- |
| Title | Mustango: Toward Controllable Text-to-Music Generation |
| Authors | Jan Melechovsky; Zixun Guo; Deepanway Ghosal; Navonil Majumder; Dorien Herremans; Soujanya Poria |
| Venue | NAACL 2024 Long Papers, 8293–8316 |
| DOI | 10.18653/v1/2024.naacl-long.459 |
| Version reviewed | ACL Anthology version of record, June 2024 |
| Primary source | https://doi.org/10.18653/v1/2024.naacl-long.459 |
| Source type | Peer-reviewed system paper |
| Reviewed | 2026-08-29 |

## Source claims assessed

- Mustango conditions text-to-music generation on chords, beats, tempo, and key
  in addition to general text.
- The paper introduces MusicBench and evaluates musical-condition adherence
  with objective and subjective procedures.
- The results concern the evaluated data, baselines, and model configuration.

## Limitations and unresolved questions

- The model renders bounded clips rather than an indefinitely responsive audio
  stream.
- Requested musical conditions may not be realized perfectly.
- Musical adherence does not establish felt emotion, usefulness, or safety.

## Allowed manuscript use

Use as peer-reviewed precedent for translating human-readable musical controls
into a controllable generator and checking the realized output.

## Prohibited manuscript use

Do not use it to claim continuous prompt interpolation, real-time steering,
exact adherence, emotional control, or clinical benefit.
